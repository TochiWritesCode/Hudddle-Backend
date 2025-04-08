from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from src.db.models import TaskStatus

class TaskSchema(BaseModel):
    id: UUID
    created_at: datetime
    updated_at: datetime
    title: str
    description: Optional[str] = None
    is_recurring: bool
    status: TaskStatus
    category: Optional[str] = None
    task_tools: Optional[List[str]] = None
    due_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_by_id: UUID
    workroom_id: Optional[UUID] = None

    class Config:
        from_attributes = True

class TaskCollaboratorSchema(BaseModel):
    task_id: UUID
    user_id: UUID
    invited_by_id: UUID

    class Config:
        from_attributes = True


class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, description="Title of the task")
    description: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING
    is_recurring: bool = False
    due_date: Optional[datetime] = None
    workroom_id: Optional[UUID] = None
    category: Optional[str] = None
    task_tools: Optional[List[str]] = None
    
class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, description="Title of the task")
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    is_recurring: bool = False
    due_date: Optional[datetime] = None
    workroom_id: Optional[UUID] = None
    category: Optional[str] = None
    task_tools: Optional[List[str]] = None