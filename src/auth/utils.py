from itsdangerous import URLSafeTimedSerializer
from sqlalchemy import select
from fastapi import WebSocket, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime, timedelta
from passlib.context import CryptContext
from src.config import Config
from src.db.models import User
import logging
import jwt
import uuid
from jwt.exceptions import ExpiredSignatureError, DecodeError


password_context = CryptContext(
    schemes=["bcrypt"]
)

serializer = URLSafeTimedSerializer(
    secret_key=Config.JWT_SECRET_KEY, salt="email-verification"
)

ACCESS_TOKEN_EXPIRY = 360000

def generate_password_hash(password: str) -> str:
    hash = password_context.hash(password)
    
    return hash

def verify_password(password: str, hash: str) -> bool:
    return password_context.verify(password, hash)

def create_access_tokens(user_data: dict, expiry: timedelta = None, refresh: bool= False):
    payload = {}
    payload["user"] = user_data
    payload["exp"] = datetime.now() + (
            expiry if expiry is not None else timedelta(seconds=ACCESS_TOKEN_EXPIRY)
        )
    payload["jti"] = str(uuid.uuid4())
    payload["refresh"] = refresh
    
    token = jwt.encode(
        payload= payload,
        key=Config.JWT_SECRET_KEY,
        algorithm=Config.JWT_ALGORITHM
    )
    return token

def decode_token(token: str) -> dict:
    try:
        token_data = jwt.decode(
            jwt=token,
            key=Config.JWT_SECRET_KEY,
            algorithms=[Config.JWT_ALGORITHM]
        )
        return token_data
    except ExpiredSignatureError:
        logging.info("Token has expired")
        return None
    except DecodeError:
        logging.info("Invalid token format")
        return None
    except jwt.PyJWTError as e:
        logging.exception(f"Other JWT error: {e}")
        return None
    
def create_url_safe_token(data: dict):

    token = serializer.dumps(data)

    return token

def decode_url_safe_token(token:str):
    try:
        token_data = serializer.loads(token)

        return token_data
    
    except Exception as e:
        logging.error(str(e))

async def get_current_user_websocket(
    websocket: WebSocket,
    token: str,
    session: AsyncSession
) -> Optional[User]:
    """Authenticate user via WebSocket connection"""
    credentials_exception = None
    
    try:
        payload = jwt.decode(jwt=token, key=Config.JWT_SECRET_KEY, algorithms=[Config.JWT_ALGORITHM])
        
        # Extract user_id from nested structure
        user_data = payload.get("user", {})
        user_id: str = user_data.get("user_uid")
        
        if user_id is None:
            credentials_exception = "Invalid token - user ID not found"
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return None
            
        # Verify user exists
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalars().first()
        if user is None:
            credentials_exception = "User not found"
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return None
        
        return user
    except ExpiredSignatureError:
        print("Token expired")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return None
    except DecodeError:
        print("Invalid token format")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return None
    except jwt.PyJWTError as e:
        print(f"JWTError: {e}")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return None