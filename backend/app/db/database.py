from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from app.core.config import settings

Base = declarative_base()

engine = create_async_engine(settings.database_url, echo=settings.sql_echo)
async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


def should_auto_create_schema() -> bool:
    return settings.environment != "production"


async def get_db():
    async with async_session_maker() as session:
        yield session


async def init_db():
    if not should_auto_create_schema():
        return
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
