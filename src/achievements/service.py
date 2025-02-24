from src.db.models import LevelCategory, LevelTier, Task, TaskCollaborator, TaskStatus, User, Badge, UserBadgeLink, UserLevel, UserStreak
from fastapi import Depends
from src.db.main import get_session
from datetime import date, timedelta
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from src.auth.dependencies import get_current_user


def determine_level_tier(points: int) -> LevelTier:
    if points < 50:
        return LevelTier.BEGINNER
    elif points < 150:
        return LevelTier.INTERMEDIATE
    elif points < 300:
        return LevelTier.ADVANCED
    else:
        return LevelTier.EXPERT


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


async def get_or_create_user_level(category: LevelCategory, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)) -> UserLevel:
    user_level = await session.exec(select(UserLevel).where(UserLevel.user_id == current_user.id, UserLevel.level_category == category))
    user_level = user_level.first()
    if not user_level:
        user_level = UserLevel(user_id=current_user.id, level_category=category, level_tier=LevelTier.BEGINNER)
        session.add(user_level)
        await session.commit()
        await session.refresh(user_level)
    return user_level

async def update_user_level(category: LevelCategory, points: int, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    user_level = await get_or_create_user_level(current_user.id, category, session)
    user_level.level_points += points
    user_level.level_tier = determine_level_tier(user_level.level_points)
    await session.commit()
    await session.refresh(user_level)

# --- Activity Tracking and Point Calculation ---

async def calculate_leader_points(current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    # Task creation: 5 points per task.
    tasks_created = await session.exec(select(Task).where(Task.created_by_id == current_user.id))
    task_creation_points = len(tasks_created.all()) * 5

    # Task delegation: 10 points per successful delegation. (Needs more complex logic)
    #Delegation logic is not implemented.
    delegation_points = 0

    return task_creation_points + delegation_points

async def calculate_workaholic_points(current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    # Task completion: 3 points per task.
    tasks_completed = await session.exec(select(Task).where(Task.created_by_id == current_user.id, Task.status == "COMPLETED"))
    task_completion_points = len(tasks_completed.all()) * 3

    # On-time completion: 2 bonus points. (Needs completed_at and due_date)
    on_time_completion_points = 0
    tasks = tasks_completed.all()
    for task in tasks:
        if task.due_date and task.completed_at and task.completed_at <= task.due_date:
            on_time_completion_points += 2

    return task_completion_points + on_time_completion_points

async def calculate_team_player_points(current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    # Task collaboration: 5 points per collaboration.
    collaborations = await session.exec(select(TaskCollaborator).where(TaskCollaborator.user_id == current_user.id))
    collaboration_points = len(collaborations.all()) * 5

    # Accepting collaboration invite: 3 points.
    invites_accepted = await session.exec(select(TaskCollaborator).where(TaskCollaborator.user_id == current_user.id, TaskCollaborator.invited_by_id != current_user.id))
    invite_points = len(invites_accepted.all()) * 3

    return collaboration_points + invite_points

async def calculate_slacker_points(current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    # Task completion below 20%: -5 points.
    tasks_created = await session.exec(select(Task).where(Task.created_by_id == current_user.id))
    tasks_completed = await session.exec(select(Task).where(Task.created_by_id == current_user.id, Task.status == "COMPLETED"))

    created_count = len(tasks_created.all())
    completed_count = len(tasks_completed.all())
    if created_count > 0 and (completed_count / created_count) < 0.2:
        task_completion_points = -5
    else:
      task_completion_points = 0
    # Daily active time below 1 hour: -3 points. (Needs activity tracking)
    #activity tracking is not implemented.
    active_time_points = 0

    return task_completion_points + active_time_points

# --- Level Update Logic ---

async def update_user_levels(current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    leader_points = await calculate_leader_points(current_user.id, session)
    workaholic_points = await calculate_workaholic_points(current_user.id, session)
    team_player_points = await calculate_team_player_points(current_user.id, session)
    slacker_points = await calculate_slacker_points(current_user.id, session)

    await update_user_level(current_user.id, LevelCategory.LEADER, leader_points, session)
    await update_user_level(current_user.id, LevelCategory.WORKAHOLIC, workaholic_points, session)
    await update_user_level(current_user.id, LevelCategory.TEAM_PLAYER, team_player_points, session)
    await update_user_level(current_user.id, LevelCategory.SLACKER, slacker_points, session)


async def update_user_streak(current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    today = date.today()
    user_streak = await session.exec(select(UserStreak).where(UserStreak.user_id == current_user.id))
    user_streak = user_streak.first()
    if not user_streak:
        user_streak = UserStreak(user_id=current_user.id)
        session.add(user_streak)
        await session.commit()
        await session.refresh(user_streak)

    if user_streak.last_active_date == today:
        return  # Already updated today

    if user_streak.last_active_date == today - timedelta(days=1):
        user_streak.current_streak += 1
    else:
        user_streak.current_streak = 1

    user_streak.last_active_date = today

    if user_streak.current_streak > user_streak.highest_streak:
        user_streak.highest_streak = user_streak.current_streak

    await session.commit()
