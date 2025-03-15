from sqlmodel import create_engine, SQLModel
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import sessionmaker
from src.config import Config

# Creating the database object as an Asynchronous engine
async_engine = AsyncEngine(
    create_engine(
        url=Config.DATABASE_URL,
        echo=True
    )
)

# Start DB engine
async def init_db():
    async with async_engine.begin() as conn:
        
        # Scans for any models initialized using SQLModel object & creates them
        await conn.run_sync(SQLModel.metadata.create_all)
        
# Returning session to be used by Routes
async def get_session() -> AsyncSession:
    Session = sessionmaker(
        bind = async_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with Session() as session:
        yield session