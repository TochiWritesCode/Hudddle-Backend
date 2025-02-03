from pydantic import BaseModel
from datetime import datetime
from typing import Optional

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
