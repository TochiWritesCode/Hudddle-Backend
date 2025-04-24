from pydantic import BaseModel, Field, EmailStr, validator
from typing import List, Optional
from uuid import UUID
from datetime import datetime

class UserSchema(BaseModel):
    id: UUID
    created_at: datetime
    updated_at: datetime
    firebase_uid: Optional[str] = None
    username: Optional[str] = None
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    password_hash: str
    role: str
    xp: int
    level: int
    badges: List[str]
    avatar_url: Optional[str] = None
    is_verified: bool
    productivity: float
    average_task_time: float
    user_type: Optional[str] = None
    find_us: Optional[str] = None
    software_used: Optional[str] = None

    class Config:
        from_attributes = True

# User Creation Schema
class UserCreateModel(BaseModel):
    email: EmailStr = Field(max_length=40, description="Email address of the user")
    password: str = Field(min_length=6, description="Password of the user")
    
class UserUpdateModel(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    avatar_url: Optional[str] = None
    is_verified: Optional[bool] = None
    username: Optional[str] = None
    user_type: Optional[str] = None
    find_us: Optional[str] = None
    software_used: Optional[List[str]] = None
    productivity: Optional[float] = None 
    average_task_time: Optional[float] = None
    
    @validator("productivity")
    def productivity_must_be_between_0_and_1(cls, value):
        if value is not None and (value < 0.0 or value > 1.0):
            raise ValueError("Productivity must be between 0.0 and 1.0")
        return value

    @validator("average_task_time")
    def average_task_time_must_be_non_negative(cls, value):
        if value is not None and value < 0.0:
            raise ValueError("Average task time must be non-negative")
        return value


# User Login Schema
class UserLoginModel(BaseModel):
    email: EmailStr = Field(max_length=40, description="Email address of the user")
    password: str = Field(min_length=6, description="Password of the user")

# Email Schema
class EmailModel(BaseModel):
    addresses: List[EmailStr] = Field(description="List of email addresses to send emails to")

# Password Reset Request Schema
class PasswordResetRequestModel(BaseModel):
    email: EmailStr = Field(description="Email address for password reset")

# Password Reset Confirmation Schema
class PasswordResetConfirmModel(BaseModel):
    new_password: str = Field(min_length=6, description="New password for the user")
    confirm_new_password: str = Field(min_length=6, description="Confirmation of the new password")
    