from typing import List
from src.db.models import Badge, UserBadgeLink
from fastapi import APIRouter, Depends
from src.db.main import get_session
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from src.db.models import User
from src.auth.dependencies import get_current_user

achievement_router = APIRouter()

# Call check_and_award_badges after updating the user's xp.

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