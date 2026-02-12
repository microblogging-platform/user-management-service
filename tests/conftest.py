from uuid import uuid4
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from testcontainers.postgres import PostgresContainer
from infrastructure.db.base import Base
from infrastructure.db.models import UserModel, GroupModel


@pytest.fixture(scope="session")
def postgres_container():
    postgres = PostgresContainer("postgres:16-alpine")
    postgres.start()

    yield postgres

    postgres.stop()


@pytest.fixture(scope="session")
async def db_engine(postgres_container):
    driver_url = postgres_container.get_connection_url()

    async_url = driver_url.replace("psycopg2", "asyncpg")

    engine = create_async_engine(async_url, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest.fixture(scope="function")
async def db_session(db_engine):

    connection = await db_engine.connect()
    transaction = await connection.begin()

    session_factory = async_sessionmaker(
        bind=connection,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )
    session = session_factory()

    yield session

    await session.close()
    await transaction.rollback()
    await connection.close()


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