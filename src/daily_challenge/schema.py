from pydantic import BaseModel
from uuid import UUID
from datetime import datetime


class DailyChallengeSchema(BaseModel):
    id: UUID
    created_at: datetime
    updated_at: datetime
    description: str
    points: int

    class Config:
        from_attributes = True
        
class UserDailyChallengeSchema(BaseModel):
    id: UUID
    user_id: UUID
    daily_challenge_id: UUID
    accepted: bool
    completed: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True