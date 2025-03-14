from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi import HTTPException, Depends, status
from fastapi.responses import JSONResponse
from src.db.models import User
from typing import Dict, Any
from .schema import UserCreateModel
from sqlmodel import select
from .utils import generate_password_hash
import logging
import asyncio
from sqlalchemy.exc import IntegrityError

class UserService:
    
    async def get_user_by_firebase_uid(self, firebase_uid: str, session: AsyncSession):
        """Retrieves a user by their Firebase UID."""
        try:
            statement = select(User).where(User.firebase_uid == firebase_uid)
            result = await session.exec(statement)
            user = result.first()
            return user
        except Exception as e:
            print(f"Error getting user by Firebase UID: {e}")
            return None

    async def get_user_by_email(self, email: str, session: AsyncSession):
        try:
            logging.info(f"Getting user by email: {email}")
            logging.info(f"Current event loop: {id(asyncio.get_running_loop())}")
            statement = select(User).where(User.email == email)
            logging.info("Executing query...")
            result = await session.execute(statement)
            logging.info("Query executed.")
            user_object = result.first()
            logging.info(f"User found: {user_object}")
            return user_object
        except Exception as e:
            logging.error(f"Error getting user by email: {e}")
            return None

    async def user_exists(self, email, session: AsyncSession):
        logging.info(f"user_exists event loop: {id(asyncio.get_running_loop())}")
        try:
            user_object = await self.get_user_by_email(email, session)
            return user_object is not None
        except Exception as e:
            logging.error(f"Error checking if user exists: {e}")
            return False

    async def create_user(self, user_data: UserCreateModel, session: AsyncSession):
        logging.info(f"create_user event loop: {id(asyncio.get_running_loop())}")
        user_data_dict = user_data.model_dump()
        new_user = User(**user_data_dict)
        new_user.password_hash = generate_password_hash(user_data_dict["password"])
        new_user.role = "user"
        session.add(new_user) 
        try:
            await session.commit()
        except IntegrityError as e:
            await session.rollback()
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"User with email {user_data.email} already exists.")
        return new_user

    async def update_user(self, user: User, user_data: dict, session: AsyncSession):
        logging.info(f"update_user event loop: {id(asyncio.get_running_loop())}")
        try:
            for key, value in user_data.items():
                setattr(user, key, value)
            session.add(user)
            await session.commit()
        except Exception as e:
            await session.rollback()
            logging.error(f"Error updating user: {e}")
            raise e
    
    
