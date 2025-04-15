from src.mail import create_message, mail
import firebase_admin
from firebase_admin import auth, credentials
from fastapi import APIRouter, Depends, status, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import timedelta, datetime
from typing import Annotated
import logging

# Import SQLAlchemy models and utilities
from src.db.models import User
from src.db.main import get_session
from .schema import (
    PasswordResetConfirmModel, PasswordResetRequestModel, 
    UserCreateModel, UserLoginModel, EmailModel, UserUpdateModel
)
from .service import UserService
from .utils import (
    create_access_tokens, create_url_safe_token, 
    decode_url_safe_token, verify_password, generate_password_hash
)
from .dependencies import RefreshTokenBearer, AccessTokenBearer, get_current_user, RoleChecker
from src.db.mongo import add_jti_to_blocklist
from src.config import Config

# Initialize Firebase Admin SDK
cred = credentials.Certificate("hudddle-project-firebase.json")
firebase_admin.initialize_app(cred)

# Router and service setup
auth_router = APIRouter()
user_service = UserService()
role_checker = RoleChecker(["admin", "user"])

# Constants
REFRESH_TOKEN_EXPIRY = 2

async def send_email(message):
    await mail.send_message(message)


@auth_router.post("/firebase_login", status_code=status.HTTP_200_OK)
async def firebase_login(id_token: str, session: AsyncSession = Depends(get_session)):
    try:
        decoded_token = auth.verify_id_token(id_token)
        uid = decoded_token['uid']
        email = decoded_token['email']
        name = decoded_token.get('name')
        picture = decoded_token.get('picture')

        user = await user_service.get_user_by_email(email, session)

        if not user:
            new_user_data = {
                "email": email,
                "username": name,
                "avatar_url": picture,
                "password_hash": "firebase_user",
                "is_verified": True,
                "firebase_uid": uid,
            }
            user = await user_service.create_user(User(**new_user_data), session)

        access_token = create_access_tokens(
            user_data={"email": user.email, "user_uid": str(user.id), "role": user.role}
        )
        refresh_token = create_access_tokens(
            user_data={"email": user.email, "user_uid": str(user.id)},
            refresh=True,
            expiry=timedelta(days=REFRESH_TOKEN_EXPIRY),
        )
        return JSONResponse(
            content={
                "message": "Login Successful",
                "access token": access_token,
                "refresh token": refresh_token,
                "user": {"email": user.email, "uid": str(user.id), "username": user.username},
            }
        )
    except auth.InvalidIdTokenError:
        raise HTTPException(status_code=401, detail="Invalid ID token")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Firebase login failed: {e}")
    finally:
        await session.close()


@auth_router.post("/signup", status_code=status.HTTP_201_CREATED)
async def create_user_account(
    user_data: UserCreateModel, 
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session)
):
    try:
        email = user_data.email
        user_exists = await user_service.user_exists(email, session)
        if user_exists:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User with email {email} already exists.",
            )

        new_user = await user_service.create_user(user_data, session)

        token = create_url_safe_token({"email": email})
        link = f"http://{Config.DOMAIN}/api/v1/auth/verify/{token}"
        html = f"""
        <h1>Verify your Email</h1>
        <p>Please click this <a href="{link}">link</a> to verify your email</p>
        """
        emails = [email]
        subject = "Verify Your email"
        message = create_message(recipients=emails, subject=subject, body=html)

        background_tasks.add_task(send_email, message)

        return {
            "message": "Account Created! Check email to verify your account",
            "user": new_user,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await session.close()


@auth_router.post("/login", status_code=status.HTTP_200_OK)
async def login_user(
    user_login_data: UserLoginModel, session: AsyncSession = Depends(get_session)
):
    try:
        email = user_login_data.email
        password = user_login_data.password

        user = await user_service.get_user_by_email(email, session)
        if user is not None:
            password_valid = verify_password(password, user.password_hash)

            if password_valid:
                access_token = create_access_tokens(
                    user_data={
                        "email": user.email,
                        "user_uid": str(user.id),
                        "role": user.role,
                    }
                )

                refresh_token = create_access_tokens(
                    user_data={
                        "email": user.email,
                        "user_uid": str(user.id),
                    },
                    refresh=True,
                    expiry=timedelta(days=REFRESH_TOKEN_EXPIRY),
                )
                return JSONResponse(
                    content={
                        "message": "Login Successful",
                        "access_token": access_token,
                        "refresh_token": refresh_token,
                        "user": {
                            "email": user.email,
                            "uid": str(user.id),
                            "username": user.username,
                        },
                    }
                )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid Email or Password",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await session.close()


@auth_router.get("/verify/{token}")
async def verify_user_account(
    token: str, session: AsyncSession = Depends(get_session)
):
    try:
        token_data = decode_url_safe_token(token)
        user_email = token_data.get("email")

        if user_email:
            user = await user_service.get_user_by_email(user_email, session)
            if not user:
                raise HTTPException(status_code=404, detail="User not found")

            await user_service.update_user(user, {"is_verified": True}, session)
            return JSONResponse(
                content={"message": "Account verified successfully"},
                status_code=status.HTTP_200_OK,
            )

        return JSONResponse(
            content={"message": "Error during verification"},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    except Exception as e:
        logging.error(f"Error verifying user account: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        await session.close()


@auth_router.get("/refresh_token")
async def get_new_access_token(token_details: dict = Depends(RefreshTokenBearer())):
    try:
        expiry_timestamp = token_details['exp']
        if datetime.fromtimestamp(expiry_timestamp) > datetime.now():
            new_access_token = create_access_tokens(user_data=token_details['user'])
            return JSONResponse(content={"access_token": new_access_token})
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or Expired Token"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@auth_router.get("/logout")
async def revoke_token(token_details: dict = Depends(AccessTokenBearer())):
    jti = token_details["jti"]
    await add_jti_to_blocklist(jti)

    return JSONResponse(
        content={"message": "Logged out Successfully"},
        status_code=status.HTTP_200_OK,
    )


@auth_router.get("/me")
async def get_current_user(
    user: User = Depends(get_current_user),
    _: bool = Depends(role_checker),
    session: AsyncSession = Depends(get_session),
):
    try:
        return user
    except Exception as e:
        logging.error(f"Error fetching current user: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        await session.close()


@auth_router.post("/password-reset-request")
async def password_reset_request(email_data: PasswordResetRequestModel, background_tasks: BackgroundTasks):
    email = email_data.email

    token = create_url_safe_token({"email": email})

    link = f"http://{Config.DOMAIN}/api/v1/auth/password-reset-confirm/{token}"

    html_message = f"""
    <h1>Reset Your Password</h1>
    <p>Please click this <a href="{link}">link</a> to Reset Your Password</p>
    """
    subject = "Reset Your Password"

    message = create_message(recipients=[email], subject=subject, body=html_message)

    background_tasks.add_task(send_email, message)

    return JSONResponse(
        content={
            "message": "Please check your email for instructions to reset your password",
        },
        status_code=status.HTTP_200_OK,
    )


@auth_router.post("/password-reset-confirm/{token}")
async def reset_account_password(
    token: str,
    passwords: PasswordResetConfirmModel,
    session: AsyncSession = Depends(get_session),
):
    try:
        new_password = passwords.new_password
        confirm_password = passwords.confirm_new_password

        if new_password != confirm_password:
            raise HTTPException(
                detail="Passwords do not match", status_code=status.HTTP_400_BAD_REQUEST
            )

        token_data = decode_url_safe_token(token)
        user_email = token_data.get("email")

        if user_email:
            user = await user_service.get_user_by_email(user_email, session)
            if not user:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

            passwd_hash = generate_password_hash(new_password)
            await user_service.update_user(user, {"password_hash": passwd_hash}, session)

            return JSONResponse(
                content={"message": "Password reset Successfully"},
                status_code=status.HTTP_200_OK,
            )

        return JSONResponse(
            content={"message": "Error occurred during password reset."},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await session.close()


@auth_router.post("/send_mail")
async def send_mail(emails: EmailModel, background_tasks: BackgroundTasks):
    emails = emails.addresses

    html = "<h1>Welcome to the app</h1>"
    subject = "Welcome to our app"

    message = create_message(recipients=emails, subject=subject, body=html)

    background_tasks.add_task(send_email, message)

    return {"message": "Email sent successfully"}


@auth_router.put("/update-profile")
async def update_user_profile(
    update_data: UserUpdateModel,
    user: User = Depends(get_current_user),
    _: bool = Depends(role_checker),
    session: AsyncSession = Depends(get_session),
):
    try:
        # Reattach the user object to the current session
        db_user = await session.merge(user)
        update_dict = update_data.dict(exclude_unset=True)
        updated_user = await user_service.update_user(db_user, update_dict, session)
        return updated_user
    except Exception as e:
        logging.error(f"Error updating user profile: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        await session.close()
        
        
        