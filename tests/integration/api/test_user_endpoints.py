from typing import AsyncIterator
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from domain.entities import User
from domain.enums import Role
from domain.interfaces.services.storage import IStorageService
from fastapi import FastAPI
from infrastructure.db import get_db_session
from infrastructure.db.repositories import SqlAlchemyUserRepository
from presentation.api.v1 import dependencies as deps
from presentation.api.v1.endpoints import user as user_endpoints
from sqlalchemy.ext.asyncio import AsyncSession


class FakeStorageService(IStorageService):
    async def upload_file(self, file, filename: str, content_type: str) -> str:  # type: ignore[override]
        return f"uploads/{filename}"

    async def delete_file(self, file_path: str) -> None:
        return None

    async def generate_presigned_upload_url(
        self, object_key: str, content_type: str, expires_in: int = 3600
    ) -> str:
        return f"https://storage.test/upload/{object_key}"

    async def generate_presigned_get_url(self, object_key: str, expires_in: int = 3600) -> str | None:
        return f"https://storage.test/get/{object_key}"


@pytest.fixture
async def persisted_user(db_session: AsyncSession) -> User:
    repo = SqlAlchemyUserRepository(db_session)
    user = User(
        name="John",
        surname="Doe",
        username=f"user_{uuid4().hex[:8]}",
        password_hash="hashed-password",
        email="john@example.com",
        phone_number="+14155552671",
        role=Role.ADMIN,
        image_s3_path="",
        is_blocked=False,
        group_id=None,
    )
    return await repo.create(user)


@pytest.fixture
async def app(db_session: AsyncSession, persisted_user: User) -> FastAPI:
    app = FastAPI()
    app.include_router(user_endpoints.router, prefix="/api/v1")

    async def override_db_session() -> AsyncIterator[AsyncSession]:
        yield db_session

    async def override_current_user() -> User:
        return persisted_user

    app.dependency_overrides[get_db_session] = override_db_session
    app.dependency_overrides[deps.get_current_user] = override_current_user
    app.dependency_overrides[deps.get_storage_service] = lambda: FakeStorageService()

    return app


@pytest.fixture
async def client(app: FastAPI) -> AsyncIterator[AsyncClient]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio(loop_scope="session")
async def test_get_me_returns_current_user(client: AsyncClient, persisted_user: User) -> None:
    response = await client.get("/api/v1/users/me")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == str(persisted_user.id)
    assert body["username"] == persisted_user.username


@pytest.mark.asyncio(loop_scope="session")
async def test_update_me_persists_changes(client: AsyncClient, db_session: AsyncSession, persisted_user: User) -> None:
    response = await client.patch("/api/v1/users/me", json={"name": "Jane"})
    assert response.status_code == 200

    repo = SqlAlchemyUserRepository(db_session)
    updated = await repo.get_by_id(persisted_user.id)

    assert updated is not None
    assert updated.name == "Jane"


@pytest.mark.asyncio(loop_scope="session")
async def test_get_user_by_id_allows_admin(client: AsyncClient, persisted_user: User) -> None:
    response = await client.get(f"/api/v1/users/{persisted_user.id}")

    assert response.status_code == 200
    assert response.json()["id"] == str(persisted_user.id)


@pytest.mark.asyncio(loop_scope="session")
async def test_get_users_returns_paginated_list(client: AsyncClient, db_session: AsyncSession, persisted_user: User) -> None:
    repo = SqlAlchemyUserRepository(db_session)
    other_user = User(
        name="Alice",
        surname="Smith",
        username=f"user_{uuid4().hex[:8]}",
        password_hash="hashed-password",
        email="alice@example.com",
        phone_number="+14155552672",
        role=Role.USER,
        image_s3_path="",
        is_blocked=False,
        group_id=None,
    )
    await repo.create(other_user)

    response = await client.get("/api/v1/users?page=1&limit=10")
    assert response.status_code == 200

    body = response.json()
    assert body["total"] >= 2
    assert isinstance(body["items"], list)
    assert any(item["id"] == str(persisted_user.id) for item in body["items"])


@pytest.mark.asyncio(loop_scope="session")
async def test_avatar_upload_url_rejects_wrong_content_type(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/users/me/avatar/upload-url",
        json={"filename": "avatar.bmp", "content_type": "image/bmp"},
    )

    assert response.status_code == 400


@pytest.mark.asyncio(loop_scope="session")
async def test_avatar_upload_url_success_uses_storage_service(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/users/me/avatar/upload-url",
        json={"filename": "avatar.png", "content_type": "image/png"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["upload_url"].startswith("https://storage.test/upload/")
    assert body["object_key"].startswith("avatars/")


@pytest.mark.asyncio(loop_scope="session")
async def test_confirm_avatar_upload_rejects_invalid_object_key(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/users/me/avatar/confirm?object_key=avatars/another-user/file.png"
    )

    assert response.status_code == 403