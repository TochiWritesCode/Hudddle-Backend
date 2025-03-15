from fastapi import Body, APIRouter, HTTPException, Depends, status, Query
from sqlmodel import select
from src.db.main import get_session
from sqlmodel.ext.asyncio.session import AsyncSession
from .service import update_workroom_leaderboard
from .schema import WorkroomCreate, WorkroomTaskCreate, WorkroomUpdate
from typing import List, Optional, Dict, Any
from uuid import UUID
from src.db.models import Workroom, User, Task, Leaderboard, TaskStatus, WorkroomMemberLink
from src.auth.dependencies import get_current_user
from datetime import datetime
from sqlmodel import delete
from sqlalchemy.orm import selectinload

workroom_router = APIRouter()

# Workroom Endpoints

@workroom_router.post("", status_code=status.HTTP_201_CREATED)
async def create_workroom(
    workroom_data: WorkroomCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    workroom_data_dict = workroom_data.model_dump()
    new_workroom = Workroom(**workroom_data_dict)
    new_workroom.created_by = current_user.id
    session.add(new_workroom)
    await session.commit()
    await session.refresh(new_workroom)
    return new_workroom

@workroom_router.get("", response_model=List[Workroom])
async def get_workrooms(session: AsyncSession = Depends(get_session), current_user: User = Depends(get_current_user)):
    workrooms = await session.exec(select(Workroom).where(Workroom.created_by == current_user.id))
    return workrooms.all()


@workroom_router.get("/{workroom_id}", response_model=Workroom)
async def get_workroom(
    workroom_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    workroom = await session.get(Workroom, workroom_id)
    if not workroom:
        raise HTTPException(status_code=404, detail="Workroom not found")
    if workroom.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this workroom")
    return workroom

@workroom_router.patch("/{workroom_id}", response_model=Workroom)
async def update_workroom(
    workroom_id: UUID,
    workroom_update: WorkroomUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    workroom = await session.get(Workroom, workroom_id)
    if not workroom:
        raise HTTPException(status_code=404, detail="Workroom not found")

    if workroom.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this workroom")

    for key, value in workroom_update.dict(exclude_unset=True).items():
        setattr(workroom, key, value)
    await session.commit()
    await session.refresh(workroom)
    return workroom

@workroom_router.delete("/{workroom_id}")
async def delete_workroom(
    workroom_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    workroom = await session.get(Workroom, workroom_id)
    if not workroom:
        raise HTTPException(status_code=404, detail="Workroom not found")
    if workroom.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this workroom")
    await session.delete(workroom)
    await session.flush()
    await session.commit()
    return {"message": "Workroom deleted successfully"}

# Membership Management

@workroom_router.post("/{workroom_id}/members")
async def add_members_to_workroom(
    workroom_id: UUID,
    user_ids: List[UUID],
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    statement = select(Workroom).options(selectinload(Workroom.members)).where(Workroom.id == workroom_id)
    result = await session.exec(statement)
    workroom = result.one_or_none()
    if not workroom:
        raise HTTPException(status_code=404, detail="Workroom not found")
    if workroom.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to add members to this workroom")
    for user_id in user_ids:
        user = await session.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail=f"User with ID {user_id} not found")
        if user in workroom.members:
            continue
        workroom.members.append(user)

    await session.commit()
    await session.refresh(workroom)
    return workroom


@workroom_router.get("/{workroom_id}/members", response_model=List[User])
async def get_workroom_members(
    workroom_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    statement = (
        select(Workroom)
        .options(selectinload(Workroom.members))
        .where(Workroom.id == workroom_id)
    )
    result = await session.exec(statement)
    workroom = result.one_or_none()
    
    if not workroom:
        raise HTTPException(status_code=404, detail="Workroom not found")
    if workroom.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view members of this workroom")

    return workroom.members

@workroom_router.delete("/{workroom_id}/members", response_model=Dict[str, str])
async def remove_members_from_workroom(
    workroom_id: UUID,
    user_ids: List[UUID] = Body(..., embed=True),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    statement = (
        select(Workroom)
        .options(selectinload(Workroom.members))
        .where(Workroom.id == workroom_id)
    )
    result = await session.exec(statement)
    workroom = result.one_or_none()

    if not workroom:
        raise HTTPException(status_code=404, detail="Workroom not found")
    if workroom.created_by != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to remove members from this workroom"
        )
    stmt = delete(WorkroomMemberLink).where(
        WorkroomMemberLink.workroom_id == workroom_id,
        WorkroomMemberLink.user_id.in_(user_ids)
    )
    result = await session.exec(stmt)
    await session.commit()
    if result.rowcount == 0:
        return {"message": f"None of the users {user_ids} were members of workroom {workroom_id}"}
    
    return {"message": f"Users {user_ids} removed from workroom {workroom_id}"}

# Task Management (Related to Workrooms)

@workroom_router.get("/{workroom_id}/tasks", response_model=List[Task])
async def get_workroom_tasks(
    workroom_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
    status: Optional[TaskStatus] = Query(None, description="Filter by task status"),
    due_date: Optional[datetime] = Query(None, description="Filter by due date"),
    # ... Add pagination parameters if needed
):
    workroom = await session.get(Workroom, workroom_id)
    if not workroom:
        raise HTTPException(status_code=404, detail="Workroom not found")
    if workroom.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access tasks for this workroom")

    query = select(Task).where(Task.workroom_id == workroom_id)

    if status:
      query = query.where(Task.status == status)
    if due_date:
      query = query.where(Task.due_date == due_date)

    tasks = await session.exec(query)
    return tasks.all()


@workroom_router.post("/{workroom_id}/tasks", response_model=Task, status_code=status.HTTP_201_CREATED)
async def create_task_in_workroom(
    workroom_id: UUID,
    task_data: WorkroomTaskCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    workroom = await session.get(Workroom, workroom_id)
    if not workroom:
        raise HTTPException(status_code=404, detail="Workroom not found")
    if workroom.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to create tasks in this workroom")

    task_data_dict = task_data.model_dump()
    new_task = Task(**task_data_dict)
    new_task.created_by_id = current_user.id
    new_task.workroom_id = workroom_id

    session.add(new_task)
    await session.commit()
    await session.refresh(new_task)
    return new_task



# Leaderboard Management (Related to Workrooms)

@workroom_router.get("/{workroom_id}/leaderboard", response_model=List[Dict[str, Any]])
async def get_workroom_leaderboard(
    workroom_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    workroom = await session.get(Workroom, workroom_id)
    if not workroom:
        raise HTTPException(status_code=404, detail="Workroom not found")
    if current_user not in workroom.members:
        raise HTTPException(status_code=403, detail="Not authorized to view the leaderboard for this workroom")

    await update_workroom_leaderboard(workroom_id, session)

    leaderboard_entries = await session.exec(select(Leaderboard).where(Leaderboard.workroom_id == workroom_id).order_by(Leaderboard.rank))
    leaderboard_entries = leaderboard_entries.all()

    return [{
        "user_id": entry.user_id,
        "username": entry.user.user.username,
        "score": entry.score,
        "teamwork_score": entry.teamwork_score,
        "rank": entry.rank,
    } for entry in leaderboard_entries]