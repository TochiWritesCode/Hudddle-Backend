from datetime import datetime
from sqlmodel import select
from fastapi import APIRouter, HTTPException, Depends
from src.db.main import get_session
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import selectinload
from typing import List
from uuid import UUID
from src.db.models import FriendLink, FriendRequest, FriendRequestStatus, User
from src.auth.dependencies import get_current_user

friend_router = APIRouter()

# Friend Endpoints

@friend_router.post("/friend-requests", response_model=FriendRequest)
async def send_friend_request(
    receiver_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    # Check that the receiver exists
    receiver = await session.get(User, receiver_id)
    if not receiver:
        raise HTTPException(status_code=404, detail="Receiver not found")

    friend_request = FriendRequest(
        sender_id=current_user.id,
        receiver_id=receiver_id,
    )
    session.add(friend_request)
    await session.commit()
    await session.refresh(friend_request)
    return friend_request


@friend_router.post("/friend-requests/{request_id}/accept")
async def accept_friend_request(
    request_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    friend_request = await session.get(FriendRequest, request_id)
    if not friend_request:
        raise HTTPException(status_code=404, detail="Friend request not found")
    if friend_request.receiver_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to accept this request")
    
    # Update the request status
    friend_request.status = FriendRequestStatus.accepted
    friend_request.updated_at = datetime.utcnow()
    session.add(friend_request)
    
    # Insert two rows in FriendLink for symmetry.
    friend_link1 = FriendLink(user_id=friend_request.sender_id, friend_id=friend_request.receiver_id)
    friend_link2 = FriendLink(user_id=friend_request.receiver_id, friend_id=friend_request.sender_id)
    session.add(friend_link1)
    session.add(friend_link2)
    
    await session.commit()
    return {"message": "Friend request accepted."}


@friend_router.get("/friends", response_model=List[User])
async def get_current_user_friends(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    statement = (
        select(User)
        .options(selectinload(User.friends))
        .where(User.id == current_user.id)
    )
    result = await session.exec(statement)
    user = result.one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user.friends

