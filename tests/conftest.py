import os
from uuid import uuid4

import pytest
from infrastructure.db.base import Base
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool
from testcontainers.postgres import PostgresContainer


@pytest.fixture(scope="session")
def postgres_container():
    os.environ.setdefault("TESTCONTAINERS_RYUK_DISABLED", "true")

    postgres = PostgresContainer("postgres:16-alpine")
    postgres.start()

    yield postgres

    postgres.stop()


@pytest.fixture(scope="session")
async def db_engine(postgres_container):
    driver_url = postgres_container.get_connection_url()

    async_url = driver_url.replace("psycopg2", "asyncpg")

    engine = create_async_engine(async_url, echo=False, poolclass=NullPool)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest.fixture(autouse=True)
async def reset_db(db_engine):
    yield

    async with db_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


@pytest.fixture(scope="function")
async def db_session(db_engine):
    session_factory = async_sessionmaker(
        bind=db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )

    async with session_factory() as session:
        try:
            yield session
        finally:
            try:
                await session.rollback()
            except Exception:
                pass


@pytest.fixture
def user_kwargs() -> dict:
    return {
        "id": uuid4(),
        "name": "John",
        "surname": "Doe",
        "username": "johnny",
        "password_hash": "hashed-password",
        "email": "john@example.com",
        "phone_number": "+14155552671",
        "role": "USER",
        "image_s3_path": "",
        "is_blocked": False,
        "group_id": None,
    }
