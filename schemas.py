from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List

# Task Schemas
class TaskCreate(BaseModel):
    name: str
    duration: int
    deadline: datetime
    tool: str
    workroom: bool
    assigned_to: Optional[str] = None

class TaskUpdate(BaseModel):
    name: Optional[str] = None
    duration: Optional[int] = None
    deadline: Optional[datetime] = None
    tool: Optional[str] = None
    status: Optional[str] = None
    workroom: Optional[bool] = None
    assigned_to: Optional[str] = None

# User Schemas
class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str  # Consider hashing before storing
    preferences: Optional[dict] = {}
    user_type: Optional[str] = ""
    find_us: Optional[str] = ""
    software_used: Optional[List[str]] = []

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    password: Optional[str] = None
    preferences: Optional[dict] = None
    user_type: Optional[str] = None
    find_us: Optional[str] = None
    software_used: Optional[List[str]] = None

