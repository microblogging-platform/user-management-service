from datetime import datetime, timezone
from uuid import uuid4

import pytest
from domain.entities import Group, User
from domain.enums import Role
from domain.exceptions import DomainError, InvalidTokenError
from infrastructure.security.jwt_service import PyJWTService
from infrastructure.security.password_hasher import Argon2Hasher


@pytest.mark.asyncio
async def test_argon2_hasher_hash_and_verify():
    hasher = Argon2Hasher()

    hashed = await hasher.hash("strong-password")

    assert hashed != "strong-password"

    is_valid = await hasher.verify("strong-password", hashed)
    assert is_valid is True

    is_invalid = await hasher.verify("wrong-password", hashed)
    assert is_invalid is False


@pytest.mark.asyncio
async def test_argon2_hasher_rejects_empty_password():
    hasher = Argon2Hasher()

    with pytest.raises(ValueError):
        await hasher.hash("")


def test_jwt_service_create_and_decode_access_token():
    service = PyJWTService()
    token = service.create_access_token({"sub": str(uuid4()), "role": Role.USER.value}, expires_delta=5)
    payload = service.decode_token(token)

    assert payload["type"] == "access"
    assert "sub" in payload
    assert "exp" in payload


def test_jwt_service_raises_on_invalid_token():
    service = PyJWTService()
    with pytest.raises(InvalidTokenError):
        service.decode_token("not-a-jwt")


def test_jwt_service_rejects_wrong_token_type():
    service = PyJWTService()
    token = service.create_refresh_token({"sub": str(uuid4())}, expires_delta=5)

    with pytest.raises(InvalidTokenError):
        service.get_user_id_from_token(token, expected_type="access")


def test_domain_entities_validation_and_defaults():
    user = User(
        id=uuid4(),
        name="Alice",
        surname="Bobson",
        username="alice123",
        password_hash="hash",
        email="alice@example.com",
        phone_number="+14155552672",
        role=Role.USER,
        image_s3_path="",
        is_blocked=False,
        group_id=None,
    )
    group = Group(name="Moderators")

    assert user.created_at <= datetime.now(timezone.utc)
    assert group.name == "Moderators"


def test_domain_error_message_property():
    err = DomainError("problem")
    assert err.message == "problem"
    assert str(err) == "problem"
