from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import main
import pytest
from domain.entities import User
from domain.enums import Role
from domain.exceptions import InvalidTokenError
from fastapi import HTTPException
from fastapi.testclient import TestClient
from main import create_app
from presentation.api.v1.dependencies import get_current_user, get_current_user_id


def test_get_current_user_id_success():
    token_service = Mock()
    user_id = uuid4()
    token_service.get_user_id_from_token.return_value = user_id

    result = get_current_user_id("token", token_service)

    assert result == user_id


def test_get_current_user_id_invalid_token():
    token_service = Mock()
    token_service.get_user_id_from_token.side_effect = InvalidTokenError("bad token")

    with pytest.raises(HTTPException) as exc:
        get_current_user_id("token", token_service)

    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_success():
    user = User(
        id=uuid4(),
        name="John",
        surname="Doe",
        username="johnny",
        password_hash="hash",
        email="john@example.com",
        phone_number="+14155552671",
        role=Role.USER,
        image_s3_path="",
        is_blocked=False,
        group_id=None,
    )
    repo = AsyncMock()
    repo.get_by_id.return_value = user

    result = await get_current_user(user.id, repo)

    assert result.id == user.id


@pytest.mark.asyncio
async def test_get_current_user_blocked_raises_403():
    user = User(
        id=uuid4(),
        name="John",
        surname="Doe",
        username="johnny",
        password_hash="hash",
        email="john@example.com",
        phone_number="+14155552671",
        role=Role.USER,
        image_s3_path="",
        is_blocked=True,
        group_id=None,
    )
    repo = AsyncMock()
    repo.get_by_id.return_value = user

    with pytest.raises(HTTPException) as exc:
        await get_current_user(user.id, repo)

    assert exc.value.status_code == 403


def test_create_app_healthcheck_endpoint(monkeypatch):
    monkeypatch.setattr(main, "init_rabbitmq", AsyncMock())
    monkeypatch.setattr(main, "close_rabbitmq", AsyncMock())
    app = create_app()

    with TestClient(app) as client:
        response = client.get("/healthcheck")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}