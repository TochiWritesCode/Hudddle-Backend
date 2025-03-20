from pydantic import BaseModel
from uuid import UUID
from typing import Optional
from datetime import datetime, date
from src.db.models import LevelCategory, LevelTier

class UserLevelSchema(BaseModel):
    id: UUID
    user_id: UUID
    level_category: LevelCategory
    level_tier: LevelTier
    level_points: int

    class Config:
        from_attributes = True
        
class AchievementSchema(BaseModel):
    id: UUID
    created_at: datetime
    updated_at: datetime
    name: str
    description: Optional[str] = None
    xp_reward: int
    badge_url: Optional[str] = None

    class Config:
        from_attributes = True
        

class UserStreakSchema(BaseModel):
    id: UUID
    user_id: UUID
    current_streak: int
    last_active_date: Optional[date] = None
    highest_streak: int

    class Config:
        from_attributes = True
        
        
class BadgeSchema(BaseModel):
    id: UUID
    created_at: datetime
    updated_at: datetime
    name: str
    description: Optional[str] = None
    image_url: Optional[str] = None

    class Config:
        from_attributes = True
        
        
class UserBadgeLinkSchema(BaseModel):
    user_id: UUID
    badge_id: UUID

    class Config:
        from_attributes = True