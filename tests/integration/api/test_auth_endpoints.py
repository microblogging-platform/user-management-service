from datetime import datetime, timezone
from typing import Any, AsyncIterator, Dict, List

import pytest
from application.dto.auth import TokenResponse
from domain.entities import User
from domain.enums import Role
from domain.interfaces.services.blacklist import ITokenBlacklistService
from domain.interfaces.services.message_broker import IMessageBroker
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from infrastructure.db import get_db_session
from infrastructure.db.repositories import SqlAlchemyUserRepository
from infrastructure.security.jwt_service import PyJWTService
from presentation.api.v1 import dependencies as deps
from presentation.api.v1.endpoints import auth
from sqlalchemy.ext.asyncio import AsyncSession


class InMemoryTokenBlacklistService(ITokenBlacklistService):
    def __init__(self) -> None:
        self._blacklisted: Dict[str, int] = {}

    async def blacklist_token(self, token: str, expires_at: int) -> None:
        self._blacklisted[token] = expires_at

    async def is_blacklisted(self, token: str) -> bool:
        now_ts = int(datetime.now(timezone.utc).timestamp())

        self._blacklisted = {t: exp for t, exp in self._blacklisted.items() if exp > now_ts}
        return token in self._blacklisted


class FakeMessageBroker(IMessageBroker):
    def __init__(self) -> None:
        self.published: List[Dict[str, Any]] = []

    async def publish(self, queue_name: str, message: Dict[str, Any]) -> None:
        self.published.append({"queue": queue_name, "message": message})


@pytest.fixture
async def persisted_user(db_session: AsyncSession, faker) -> User:
    repo = SqlAlchemyUserRepository(db_session)
    user = User(
        name=faker.first_name(),
        surname=faker.last_name(),
        username=faker.user_name(),
        password_hash=faker.password(),
        email=faker.email(),
        phone_number=faker.phone_number(),
        role=Role.USER,
        image_s3_path="",
        is_blocked=False,
        group_id=None,
    )
    return await repo.create(user)


@pytest.fixture
async def app(db_session: AsyncSession) -> FastAPI:
    app = create_app()

    async def override_db_session() -> AsyncIterator[AsyncSession]:
        yield db_session

    blacklist_service = InMemoryTokenBlacklistService()
    message_broker = FakeMessageBroker()

    app.dependency_overrides[get_db_session] = override_db_session
    app.dependency_overrides[deps.get_token_blacklist_service] = lambda: blacklist_service
    app.dependency_overrides[deps.get_message_broker] = lambda: message_broker

    return app


@pytest.fixture
async def client(app: FastAPI) -> AsyncIterator[AsyncClient]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio(loop_scope="session")
async def test_signup_creates_user_in_test_db(client: AsyncClient, db_session: AsyncSession) -> None:
    payload = {
        "name": "John",
        "surname": "Doe",
        "username": "signup_user",
        "password": "secret123",
        "email": "signup@example.com",
        "phone_number": "+14155552671",
    }

    response = await client.post("/api/v1/auth/signup", json=payload)

    assert response.status_code == 201

    repo = SqlAlchemyUserRepository(db_session)
    created = await repo.get_by_username("signup_user")
    assert created is not None
    assert created.email == "signup@example.com"


@pytest.mark.asyncio(loop_scope="session")
async def test_signup_duplicate_user_returns_conflict(client: AsyncClient) -> None:
    payload = {
        "name": "John",
        "surname": "Doe",
        "username": "dup_user",
        "password": "secret123",
        "email": "dup@example.com",
        "phone_number": "+14155552671",
    }

    first = await client.post("/api/v1/auth/signup", json=payload)
    assert first.status_code == 201

    second = await client.post("/api/v1/auth/signup", json=payload)
    assert second.status_code == 409


@pytest.mark.asyncio(loop_scope="session")
async def test_login_success_returns_valid_tokens(client: AsyncClient) -> None:
    signup_payload = {
        "name": "John",
        "surname": "Doe",
        "username": "login_user",
        "password": "secret123",
        "email": "login@example.com",
        "phone_number": "+14155552671",
    }
    resp = await client.post("/api/v1/auth/signup", json=signup_payload)
    assert resp.status_code == 201

    login_resp = await client.post(
        "/api/v1/auth/login",
        data={"username": "login_user", "password": "secret123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    assert login_resp.status_code == 200
    data = TokenResponse(**login_resp.json())
    assert data.access_token
    assert data.refresh_token

    jwt_service = PyJWTService()
    payload = jwt_service.decode_token(data.access_token)
    assert payload["type"] == "access"
    assert payload["sub"]


@pytest.mark.asyncio(loop_scope="session")
async def test_login_invalid_credentials_returns_401(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": "nonexistent", "password": "wrong"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    assert response.status_code == 401


@pytest.mark.asyncio(loop_scope="session")
async def test_refresh_token_invalid_returns_401(client: AsyncClient) -> None:
    response = await client.post("/api/v1/auth/refresh-token", json={"refresh_token": "bad"})
    assert response.status_code == 401


@pytest.mark.asyncio(loop_scope="session")
async def test_request_password_reset_publishes_message(client: AsyncClient, app: FastAPI) -> None:
    signup_payload = {
        "name": "John",
        "surname": "Doe",
        "username": "reset_request_user",
        "password": "secret123",
        "email": "john@example.com",
        "phone_number": "+14155552671",
    }
    resp = await client.post("/api/v1/auth/signup", json=signup_payload)
    assert resp.status_code == 201

    broker: FakeMessageBroker = app.dependency_overrides[deps.get_message_broker]()  # type: ignore[assignment]

    response = await client.post("/api/v1/auth/request-password-reset", json={"login": "john@example.com"})

    assert response.status_code == 200
    assert "reset link has been sent" in response.json()["detail"]
    assert len(broker.published) >= 1


@pytest.mark.asyncio(loop_scope="session")
async def test_reset_password_allows_login_with_new_password(client: AsyncClient, db_session: AsyncSession) -> None:
    signup_payload = {
        "name": "John",
        "surname": "Doe",
        "username": "reset_user",
        "password": "oldpassword123",
        "email": "reset@example.com",
        "phone_number": "+14155552671",
    }
    resp = await client.post("/api/v1/auth/signup", json=signup_payload)
    assert resp.status_code == 201

    repo = SqlAlchemyUserRepository(db_session)
    user = await repo.get_by_username("reset_user")
    assert user is not None

    jwt_service = PyJWTService()
    reset_token = jwt_service.create_reset_token({"sub": str(user.id)})

    reset_resp = await client.post(
        "/api/v1/auth/reset-password",
        json={"token": reset_token, "new_password": "newpassword123"},
    )
    assert reset_resp.status_code == 200

    login_resp = await client.post(
        "/api/v1/auth/login",
        data={"username": "reset_user", "password": "newpassword123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert login_resp.status_code == 200
