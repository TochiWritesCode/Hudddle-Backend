from src.db.models import Task, TaskStatus, User
from src.db.models import Badge, UserBadgeLink
from fastapi import Depends
from src.db.main import get_session
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from src.db.models import User


async def award_badge(user: User, badge: Badge, session: AsyncSession = Depends(get_session)):
    user_badge = UserBadgeLink(user_id=user.id, badge_id=badge.id)
    session.add(user_badge)
    await session.commit()
    await session.refresh(user_badge)

# This needs a long logic
async def check_and_award_badges(user: User, session: AsyncSession = Depends(get_session)):
    # Example: Award a badge for completing 10 tasks
    completed_tasks_count = await session.exec(select(Task).where(Task.created_by_id == user.id, Task.status == TaskStatus.COMPLETED))
    completed_tasks_count = len(completed_tasks_count.all())
    if completed_tasks_count >= 10:
        badge = await session.exec(select(Badge).where(Badge.name == "Task Master"))
        badge = badge.first()
        if badge:
            # Check if the user already has the badge
            user_has_badge = await session.exec(select(UserBadgeLink).where(UserBadgeLink.user_id == user.id, UserBadgeLink.badge_id == badge.id))
            if not user_has_badge.first():
                await award_badge(user, badge, session)