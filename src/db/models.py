from sqlmodel import SQLModel, Field, Column, Relationship, String
from typing import List, Optional
from datetime import datetime, date
from enum import Enum
from sqlalchemy import DateTime
from uuid import UUID, uuid4
import sqlalchemy.dialects.postgresql as pg



def create_datetime_column():
    return DateTime(timezone=False)

class TaskStatus(str, Enum):
    TODO = "TODO"
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    
class FriendRequestStatus(str, Enum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"
    
class LevelCategory(str, Enum):
    LEADER = "Leader"
    WORKAHOLIC = "Workaholic"
    TEAM_PLAYER = "Team Player"
    SLACKER = "Slacker"

class LevelTier(str, Enum):
    BEGINNER = "Beginner"
    INTERMEDIATE = "Intermediate"
    ADVANCED = "Advanced"
    EXPERT = "Expert"

class UserLevel(SQLModel, table=True):
    __tablename__ = "user_levels"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", nullable=False)
    level_category: LevelCategory
    level_tier: LevelTier
    level_points: int = Field(default=0)

    user: "User" = Relationship(back_populates="levels")
    
class FriendLink(SQLModel, table=True):
    __tablename__ = "friend_links"

    user_id: UUID = Field(foreign_key="users.id", primary_key=True)
    friend_id: UUID = Field(foreign_key="users.id", primary_key=True)
    
    
class WorkroomMemberLink(SQLModel, table=True):
    __tablename__ = "workroom_member_links"
    
    workroom_id: Optional[UUID] = Field(
        default=None, foreign_key="workrooms.id", primary_key=True
    )
    user_id: Optional[UUID] = Field(
        default=None, foreign_key="users.id", primary_key=True
    )
    
class TaskCollaborator(SQLModel, table=True):
    __tablename__ = "task_collaborators"

    task_id: UUID = Field(foreign_key="tasks.id", primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", primary_key=True)
    invited_by_id: UUID = Field(foreign_key="users.id")

    task: "Task" = Relationship(back_populates="collaborators")
    invited_by: "User" = Relationship(
        back_populates="task_collaborations_invited",
        sa_relationship_kwargs={"foreign_keys": "TaskCollaborator.invited_by_id"}
    )
    user: "User" = Relationship(
        back_populates="task_collaborations_user",
        sa_relationship_kwargs={"foreign_keys": "TaskCollaborator.user_id"}
    )


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, sa_column=create_datetime_column())
    updated_at: datetime = Field(default_factory=datetime.utcnow, sa_column=create_datetime_column())

    firebase_uid: Optional[str] = Field(default=None, index=True)
    username: Optional[str] = Field(index=True, nullable=True)
    email: str = Field(unique=True, index=True, nullable=False)
    first_name: Optional[str] = Field(default=None)
    last_name: Optional[str] = Field(default=None)
    password_hash: str = Field(nullable=False)
    role: str = Field(default="member", nullable=False)
    xp: int = Field(default=0, nullable=False)
    level: int = Field(default=1, nullable=False)
    badges: List[str] = Field(default_factory=list, sa_column=Column(pg.ARRAY(String)))
    avatar_url: Optional[str] = Field(default=None)
    is_verified: bool = Field(default=False, nullable=False)
    productivity: float = Field(default=0.0, nullable=False)
    average_task_time: float = Field(default=0.0, nullable=False)

    user_type: Optional[str] = Field(default=None)
    find_us: Optional[str] = Field(default=None)
    software_used: Optional[str] = Field(default=None)

    workrooms: List["Workroom"] = Relationship(
        back_populates="members", link_model=WorkroomMemberLink
    )
    levels: List["UserLevel"] = Relationship(back_populates="user")
    task_collaborations_invited: List["TaskCollaborator"] = Relationship(
        back_populates="invited_by",
        sa_relationship_kwargs={"foreign_keys": "TaskCollaborator.invited_by_id"}
    )
    task_collaborations_user: List["TaskCollaborator"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"foreign_keys": "TaskCollaborator.user_id"}
    )
    streak: Optional["UserStreak"] = Relationship(back_populates="user")
    created_tasks: List["Task"] = Relationship(back_populates="created_by")
    leaderboards: List["Leaderboard"] = Relationship(back_populates="user")
    friends: List["User"] = Relationship(
        link_model=FriendLink,
        sa_relationship_kwargs={
            "primaryjoin": "User.id==FriendLink.user_id",
            "secondaryjoin": "User.id==FriendLink.friend_id",
        }
    )
    
    
class FriendRequest(SQLModel, table=True):
    __tablename__ = "friend_requests"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    sender_id: UUID = Field(foreign_key="users.id", nullable=False)
    receiver_id: UUID = Field(foreign_key="users.id", nullable=False)
    status: FriendRequestStatus = Field(
        default=FriendRequestStatus.pending, nullable=False
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    

class Workroom(SQLModel, table=True):
    __tablename__ = "workrooms"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, sa_column=create_datetime_column())
    updated_at: datetime = Field(default_factory=datetime.utcnow, sa_column=create_datetime_column())

    name: str = Field(index=True, nullable=False)
    description: Optional[str] = Field(default=None)
    created_by: UUID = Field(foreign_key="users.id", nullable=False)

    members: List[User] = Relationship(
        back_populates="workrooms", link_model=WorkroomMemberLink
    )
    tasks: List["Task"] = Relationship(back_populates="workroom")
    leaderboards: List["Leaderboard"] = Relationship(back_populates="workroom")


class Task(SQLModel, table=True):
    __tablename__ = "tasks"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, sa_column=create_datetime_column())
    updated_at: datetime = Field(default_factory=datetime.utcnow, sa_column=create_datetime_column())

    title: str = Field(index=True, nullable=False)
    description: Optional[str] = Field(default=None)
    status: TaskStatus = Field(default=TaskStatus.PENDING, nullable=False)
    due_date: Optional[datetime] = Field(default=None, description="Due date in UTC")
    completed_at: Optional[datetime] = Field(default=None, sa_column=create_datetime_column())
    collaborators: List["TaskCollaborator"] = Relationship(back_populates="task")
    created_by_id: UUID = Field(foreign_key="users.id", nullable=False)
    workroom_id: Optional[UUID] = Field(foreign_key="workrooms.id", default=None)
    created_by: "User" = Relationship(back_populates="created_tasks")
    workroom: Optional["Workroom"] = Relationship(back_populates="tasks")

class Achievement(SQLModel, table=True):
    __tablename__ = "achievements"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, sa_column=create_datetime_column())
    updated_at: datetime = Field(default_factory=datetime.utcnow, sa_column=create_datetime_column())

    name: str = Field(index=True, nullable=False)
    description: Optional[str] = Field(default=None)
    xp_reward: int = Field(default=0, nullable=False)
    badge_url: Optional[str] = Field(default=None)

class Leaderboard(SQLModel, table=True):
    __tablename__ = "leaderboards"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, sa_column=create_datetime_column())
    updated_at: datetime = Field(default_factory=datetime.utcnow, sa_column=create_datetime_column())

    workroom_id: UUID = Field(foreign_key="workrooms.id", nullable=False)
    user_id: UUID = Field(foreign_key="users.id", nullable=False)
    score: int = Field(default=0, nullable=False)
    teamwork_score: int = Field(default=0, nullable=False)
    rank: Optional[int] = Field(default=None)

    workroom: Workroom = Relationship(back_populates="leaderboards")
    user: User = Relationship(back_populates="leaderboards")

class DailyChallenge(SQLModel, table=True):
    __tablename__ = "daily_challenges"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, sa_column=create_datetime_column())
    updated_at: datetime = Field(default_factory=datetime.utcnow, sa_column=create_datetime_column())

    description: str = Field(index=True, nullable=False)
    points: int = Field(default=0, nullable=False)

class UserDailyChallenge(SQLModel, table=True):
    __tablename__ = "user_daily_challenges"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", nullable=False)
    daily_challenge_id: UUID = Field(foreign_key="daily_challenges.id", nullable=False)
    accepted: bool = Field(default=False)
    completed: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow, sa_column=create_datetime_column())
    updated_at: datetime = Field(default_factory=datetime.utcnow, sa_column=create_datetime_column())

    user: "User" = Relationship()
    daily_challenge: "DailyChallenge" = Relationship()
    
    
class UserStreak(SQLModel, table=True):
    __tablename__ = "user_streaks"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", nullable=False)
    current_streak: int = Field(default=0)
    last_active_date: Optional[date] = Field(default=None)
    highest_streak: int = Field(default=0)

    user: "User" = Relationship(back_populates="streak")


class Badge(SQLModel, table=True):
    __tablename__ = "badges"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, sa_column=create_datetime_column())
    updated_at: datetime = Field(default_factory=datetime.utcnow, sa_column=create_datetime_column())

    name: str = Field(index=True, nullable=False)
    description: Optional[str] = Field(default=None)
    image_url: Optional[str] = Field(default=None)

class UserBadgeLink(SQLModel, table=True):
    __tablename__ = "user_badge_links"

    user_id: UUID = Field(foreign_key="users.id", primary_key=True)
    badge_id: UUID = Field(foreign_key="badges.id", primary_key=True)

    
