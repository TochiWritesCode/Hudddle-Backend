from pydantic import BaseModel, Field
from typing import Optional
from src.db.models import TaskStatus
from datetime import datetime


class WorkroomCreate(BaseModel):
    name: str = Field(..., min_length=1)
    description: Optional[str] = None

class WorkroomUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1)
    description: Optional[str] = None


class WorkroomTaskCreate(BaseModel):
    title: str = Field(..., min_length=1, description="Title of the task")
    description: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING
    due_date: Optional[datetime] = None