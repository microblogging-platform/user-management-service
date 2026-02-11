import os
import sys
from pathlib import Path
from uuid import uuid4

import pytest


def _set_test_env() -> None:
    defaults = {
        "FRONTEND_URL": "http://frontend.test",
        "POSTGRES_USER": "postgres",
        "POSTGRES_PASSWORD": "postgres",
        "POSTGRES_DB": "users",
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
