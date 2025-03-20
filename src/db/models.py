from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, DateTime, Enum, ARRAY, Boolean, Date
from sqlalchemy.orm import relationship
import sqlalchemy.dialects.postgresql as pg
from datetime import datetime
from enum import Enum as PyEnum
from uuid import uuid4
from .main import Base

def create_datetime_column():
    return DateTime(timezone=False)

class TaskStatus(str, PyEnum):
    TODO = "TODO"
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    
class FriendRequestStatus(str, PyEnum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"
    
class LevelCategory(str, PyEnum):
    LEADER = "Leader"
    WORKAHOLIC = "Workaholic"
    TEAM_PLAYER = "Team Player"
    SLACKER = "Slacker"

class LevelTier(str, PyEnum):
    BEGINNER = "Beginner"
    INTERMEDIATE = "Intermediate"
    ADVANCED = "Advanced"
    EXPERT = "Expert"

class UserLevel(Base):
    __tablename__ = "user_levels"

    id = Column(pg.UUID(as_uuid=True), default=uuid4, primary_key=True)
    user_id = Column(pg.UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    level_category = Column(Enum(LevelCategory))
    level_tier = Column(Enum(LevelTier))
    level_points = Column(Integer, default=0)

    user = relationship("User", back_populates="levels")
    
class FriendLink(Base):
    __tablename__ = "friend_links"

    user_id = Column(pg.UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    friend_id = Column(pg.UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    
    
class WorkroomMemberLink(Base):
    __tablename__ = "workroom_member_links"
    
    workroom_id = Column(pg.UUID(as_uuid=True), ForeignKey("workrooms.id"), primary_key=True)
    user_id = Column(pg.UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    
class TaskCollaborator(Base):
    __tablename__ = "task_collaborators"

    task_id = Column(pg.UUID(as_uuid=True), ForeignKey("tasks.id"), primary_key=True)
    user_id = Column(pg.UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    invited_by_id = Column(pg.UUID(as_uuid=True), ForeignKey("users.id"))

    task = relationship("Task", back_populates="collaborators")
    invited_by = relationship(
        "User", 
        back_populates="task_collaborations_invited",
        foreign_keys=[invited_by_id]
    )
    user = relationship(
        "User", 
        back_populates="task_collaborations_user",
        foreign_keys=[user_id]
    )


class User(Base):
    __tablename__ = "users"

    id = Column(pg.UUID(as_uuid=True), default=uuid4, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    firebase_uid = Column(String, index=True, nullable=True)
    username = Column(String, index=True, nullable=True)
    email = Column(String, unique=True, index=True, nullable=False)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="member", nullable=False)
    xp = Column(Integer, default=0, nullable=False)
    level = Column(Integer, default=1, nullable=False)
    badges = Column(ARRAY(String), default=[])
    avatar_url = Column(String, nullable=True)
    is_verified = Column(Boolean, default=False, nullable=False)
    productivity = Column(Numeric, default=0.0, nullable=False)
    average_task_time = Column(Numeric, default=0.0, nullable=False)

    user_type = Column(String, nullable=True)
    find_us = Column(String, nullable=True)
    software_used = Column(String, nullable=True)

    workrooms = relationship(
        "Workroom", 
        secondary="workroom_member_links", 
        back_populates="members"
    )
    levels = relationship("UserLevel", back_populates="user")
    task_collaborations_invited = relationship(
        "TaskCollaborator", 
        back_populates="invited_by",
        foreign_keys="[TaskCollaborator.invited_by_id]"
    )
    task_collaborations_user = relationship(
        "TaskCollaborator", 
        back_populates="user",
        foreign_keys="[TaskCollaborator.user_id]"
    )
    streak = relationship("UserStreak", back_populates="user", uselist=False)
    created_tasks = relationship("Task", back_populates="created_by")
    leaderboards = relationship("Leaderboard", back_populates="user")
    friends = relationship(
        "User", 
        secondary="friend_links", 
        primaryjoin="User.id==FriendLink.user_id",
        secondaryjoin="User.id==FriendLink.friend_id",
    )
    
    
class FriendRequest(Base):
    __tablename__ = "friend_requests"

    id = Column(pg.UUID(as_uuid=True), default=uuid4, primary_key=True)
    sender_id = Column(pg.UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    receiver_id = Column(pg.UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    status = Column(Enum(FriendRequestStatus), default=FriendRequestStatus.pending, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    

class Workroom(Base):
    __tablename__ = "workrooms"

    id = Column(pg.UUID(as_uuid=True), default=uuid4, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    name = Column(String, index=True, nullable=False)
    description = Column(String, nullable=True)
    created_by = Column(pg.UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    members = relationship(
        "User", 
        secondary="workroom_member_links", 
        back_populates="workrooms"
    )
    tasks = relationship("Task", back_populates="workroom")
    leaderboards = relationship("Leaderboard", back_populates="workroom")


class Task(Base):
    __tablename__ = "tasks"

    id = Column(pg.UUID(as_uuid=True), default=uuid4, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    title = Column(String, index=True, nullable=False)
    description = Column(String, nullable=True)
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING, nullable=False)
    due_date = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    collaborators = relationship("TaskCollaborator", back_populates="task")
    created_by_id = Column(pg.UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    workroom_id = Column(pg.UUID(as_uuid=True), ForeignKey("workrooms.id"), nullable=True)
    created_by = relationship("User", back_populates="created_tasks")
    workroom = relationship("Workroom", back_populates="tasks")

class Achievement(Base):
    __tablename__ = "achievements"

    id = Column(pg.UUID(as_uuid=True), default=uuid4, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    name = Column(String, index=True, nullable=False)
    description = Column(String, nullable=True)
    xp_reward = Column(Integer, default=0, nullable=False)
    badge_url = Column(String, nullable=True)

class Leaderboard(Base):
    __tablename__ = "leaderboards"

    id = Column(pg.UUID(as_uuid=True), default=uuid4, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    workroom_id = Column(pg.UUID(as_uuid=True), ForeignKey("workrooms.id"), nullable=False)
    user_id = Column(pg.UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    score = Column(Integer, default=0, nullable=False)
    teamwork_score = Column(Integer, default=0, nullable=False)
    rank = Column(Integer, nullable=True)

    workroom = relationship("Workroom", back_populates="leaderboards")
    user = relationship("User", back_populates="leaderboards")

class DailyChallenge(Base):
    __tablename__ = "daily_challenges"

    id = Column(pg.UUID(as_uuid=True), default=uuid4, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    description = Column(String, index=True, nullable=False)
    points = Column(Integer, default=0, nullable=False)

class UserDailyChallenge(Base):
    __tablename__ = "user_daily_challenges"

    id = Column(pg.UUID(as_uuid=True), default=uuid4, primary_key=True)
    user_id = Column(pg.UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    daily_challenge_id = Column(pg.UUID(as_uuid=True), ForeignKey("daily_challenges.id"), nullable=False)
    accepted = Column(Boolean, default=False)
    completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User")
    daily_challenge = relationship("DailyChallenge")
    
    
class UserStreak(Base):
    __tablename__ = "user_streaks"

    id = Column(pg.UUID(as_uuid=True), default=uuid4, primary_key=True)
    user_id = Column(pg.UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    current_streak = Column(Integer, default=0)
    last_active_date = Column(Date, nullable=True)
    highest_streak = Column(Integer, default=0)

    user = relationship("User", back_populates="streak")


class Badge(Base):
    __tablename__ = "badges"

    id = Column(pg.UUID(as_uuid=True), default=uuid4, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    name = Column(String, index=True, nullable=False)
    description = Column(String, nullable=True)
    image_url = Column(String, nullable=True)

class UserBadgeLink(Base):
    __tablename__ = "user_badge_links"

    user_id = Column(pg.UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    badge_id = Column(pg.UUID(as_uuid=True), ForeignKey("badges.id"), primary_key=True)