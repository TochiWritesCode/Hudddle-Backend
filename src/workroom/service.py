from fastapi import Depends, HTTPException
from sqlmodel import select
from src.db.models import TaskStatus, Workroom, Leaderboard, TaskCollaborator, Task
from src.db.main import get_session
from sqlmodel.ext.asyncio.session import AsyncSession
from uuid import UUID
from src.tasks.service import calculate_task_points



async def update_workroom_leaderboard(workroom_id: UUID, session: AsyncSession = Depends(get_session)):
    workroom = await session.get(Workroom, workroom_id)
    if not workroom:
        raise HTTPException(status_code=404, detail="Workroom not found")

    leaderboard_data = []
    for member in workroom.members:
        # Calculate total xp within the workroom
        total_xp = 0
        workroom_tasks = await session.exec(select(Task).where(Task.workroom_id == workroom_id, Task.created_by_id == member.id, Task.status == TaskStatus.COMPLETED))
        workroom_tasks = workroom_tasks.all()
        for task in workroom_tasks:
            total_xp += calculate_task_points(task) # using the function from previous steps.

        # Calculate total teamwork points within the workroom
        teamwork_points = 0
        collaborations = await session.exec(select(TaskCollaborator).join(Task).where(TaskCollaborator.user_id == member.id, Task.workroom_id == workroom_id))
        collaborations = collaborations.all()
        for collaboration in collaborations:
            task = await session.get(Task, collaboration.task_id)
            if task.status == TaskStatus.COMPLETED:
                teamwork_points += 5  # 5 points per collaboration.

        leaderboard_data.append({
            "user_id": member.id,
            "username": member.username,
            "score": total_xp,
            "teamwork_score": teamwork_points,
        })

    # Sort and update leaderboard (same as before)
    leaderboard_data.sort(key=lambda x: (-x["score"], -x["teamwork_score"], x["username"]))

    for rank, entry in enumerate(leaderboard_data, start=1):
        leaderboard_entry = await session.exec(select(Leaderboard).where(Leaderboard.workroom_id == workroom_id, Leaderboard.user_id == entry["user_id"]))
        leaderboard_entry = leaderboard_entry.first()

        if leaderboard_entry:
            leaderboard_entry.score = entry["score"]
            leaderboard_entry.teamwork_score = entry["teamwork_score"]
            leaderboard_entry.rank = rank
        else:
            new_leaderboard_entry = Leaderboard(
                workroom_id=workroom_id,
                user_id=entry["user_id"],
                score=entry["score"],
                teamwork_score=entry["teamwork_score"],
                rank=rank,
            )
            session.add(new_leaderboard_entry)

    await session.commit()