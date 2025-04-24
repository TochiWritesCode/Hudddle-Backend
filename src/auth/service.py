from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status
from src.db.models import User
from typing import Any
from .schema import UserCreateModel
from .utils import generate_password_hash
import logging
from sqlalchemy.exc import IntegrityError

class UserService:
    
    async def get_user_by_firebase_uid(self, firebase_uid: str, session: AsyncSession):
        """Retrieves a user by their Firebase UID."""
        try:
            # Use SQLAlchemy's select statement
            stmt = select(User).where(User.firebase_uid == firebase_uid)
            result = await session.execute(stmt)
            user = result.scalars().first()
            return user
        except Exception as e:
            logging.error(f"Error getting user by Firebase UID: {e}")
            return None

    async def get_user_by_email(self, email: str, session: AsyncSession):
        try:
            # Use SQLAlchemy's select statement
            stmt = select(User).where(User.email == email)
            result = await session.execute(stmt)
            user_object = result.scalars().first()
            return user_object
        except Exception as e:
            logging.error(f"Error getting user by email: {e}")
            return None

    async def user_exists(self, email: str, session: AsyncSession):
        try:
            user_object = await self.get_user_by_email(email, session)
            return user_object is not None
        except Exception as e:
            logging.error(f"Error checking if user exists: {e}")
            return False

    async def create_user(self, user_data: UserCreateModel, session: AsyncSession):
        user_data_dict = user_data.model_dump()
        password = user_data_dict.pop("password")
        new_user = User(**user_data_dict)
        new_user.password_hash = generate_password_hash(password)
        new_user.role = "user"
        session.add(new_user)
        try:
            await session.commit()
            await session.refresh(new_user)
        except IntegrityError as e:
            await session.rollback()
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User with email {user_data.email} already exists."
            )
        return new_user

    async def update_user(self, user: User, user_data: dict, session: AsyncSession):
        try:
            for key, value in user_data.items():
                setattr(user, key, value)
            await session.commit()
            await session.refresh(user)
            return user
        except Exception as e:
            await session.rollback()
            logging.error(f"Error updating user: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An error occurred while updating the user."
            )
            