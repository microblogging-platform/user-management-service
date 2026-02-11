import os
import sys
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text

def _set_test_env() -> None:
    defaults = {
        "ENVIRONMENT": "test",
        "FRONTEND_URL": "http://frontend.test",
        "POSTGRES_USER": "postgres",
        "POSTGRES_PASSWORD": "postgres",
        "POSTGRES_DB": "users",
        "POSTGRES_TEST_DB": "test_db",
        "POSTGRES_PORT": "5432",
        "POSTGRES_HOST": "localhost",
        "REDIS_HOST": "localhost",
        "REDIS_PORT": "6379",
        "REDIS_DB": "0",
        "RABBITMQ_USER": "guest",
        "RABBITMQ_PASSWORD": "guest",
        "RABBITMQ_HOST": "localhost",
        "RABBITMQ_PORT": "5672",
        "RABBITMQ_VHOST": "/",
        "JWT_SECRET_KEY": "test-secret",
        "JWT_ALGORITHM": "HS256",
        "ACCESS_TOKEN_EXPIRE_MINUTES": "15",
        "REFRESH_TOKEN_EXPIRE_MINUTES": "60",
        "PASSWORD_RESET_TOKEN_EXPIRE_MINUTES": "30",
        "AWS_ACCESS_KEY_ID": "test",
        "AWS_SECRET_ACCESS_KEY": "test",
        "AWS_REGION": "eu-central-1",
        "S3_BUCKET_NAME": "bucket-test",
    }
    for key, value in defaults.items():
        os.environ.setdefault(key, value)

_set_test_env()

SRC_PATH = Path(__file__).resolve().parents[1] / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from infrastructure.config import settings
from infrastructure.db.base import Base

def get_root_database_url():
    url = settings.test_database_url
    if "/test_db" in url:
        return url.replace("/test_db", "/postgres")
    return url.rsplit("/", 1)[0] + "/postgres"


@pytest.fixture(scope="session")
async def db_engine():
    root_url = settings.test_database_url.replace(f"/{settings.postgres_test_db}", "/postgres")
    root_engine = create_async_engine(root_url, isolation_level="AUTOCOMMIT")

    async with root_engine.connect() as conn:
        await conn.execute(text(f"DROP DATABASE IF EXISTS {settings.postgres_test_db}"))
        await conn.execute(text(f"CREATE DATABASE {settings.postgres_test_db}"))
    await root_engine.dispose()

    engine = create_async_engine(settings.test_database_url, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
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