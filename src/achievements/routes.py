from typing import List, Dict, Any
from src.db.models import Badge, UserBadgeLink, UserLevel
from fastapi import APIRouter, Depends
from src.db.main import get_session
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from .service import update_user_levels
from src.db.models import User
from src.auth.dependencies import get_current_user

achievement_router = APIRouter()


@achievement_router.get("/badges", response_model=List[Badge])
async def get_all_badges(session: AsyncSession = Depends(get_session)):
    badges = await session.exec(select(Badge))
    return badges.all()

@achievement_router.get("/users/me/badges", response_model=List[Badge])
async def get_current_user_badges(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    user_badges = await session.exec(
        select(Badge).join(UserBadgeLink).where(UserBadgeLink.user_id == current_user.id)
    )
    return user_badges.all()

@achievement_router.get("/users/me/levels", response_model=List[Dict[str, Any]])
async def get_user_levels(current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    await update_user_levels(current_user.id, session) #update levels before returning them.
    user_levels = await session.exec(select(UserLevel).where(UserLevel.user_id == current_user.id))
    return [{
        "category": level.level_category,
        "tier": level.level_tier,
        "points": level.level_points,
    } for level in user_levels.all()]

@achievement_router.get("/levels", response_model=List[Dict[str, Any]])
async def get_all_user_levels(session: AsyncSession = Depends(get_session)):
    user_levels = await session.exec(select(UserLevel))
    return [{
        "user_id": level.user_id,
        "category": level.level_category,
        "tier": level.level_tier,
        "points": level.level_points,
    } for level in user_levels.all()]