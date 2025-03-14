import asyncio
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlmodel import SQLModel
from sqlalchemy.orm import sessionmaker
from src.config import Config

# Create the async engine
async_engine = create_async_engine(
    url=Config.DATABASE_URL,
    echo=True,
    pool_size=20,
    max_overflow=10,
    pool_recycle=3600,
    pool_pre_ping=True,
    future=True,
)

# Create a sessionmaker instance
AsyncSessionLocal = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def init_db():
    """Initialize the database by creating all tables."""
    async with async_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

async def get_session() -> AsyncSession:
    """Dependency to get an async database session."""
    logging.info(f"get_session event loop: {id(asyncio.get_running_loop())}")
    async with AsyncSessionLocal() as session:
        yield session
        logging.info(f"get_session session closed event loop: {id(asyncio.get_running_loop())}")
