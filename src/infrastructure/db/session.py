from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine,  async_sessionmaker, AsyncSession
from ..config import settings

DATABASE_URL = settings.database_url

engine = create_async_engine(
    DATABASE_URL,
    echo=True,
)

async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()