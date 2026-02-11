from unittest.mock import AsyncMock
from uuid import uuid4

from domain.entities import User
from domain.enums import Role
from domain.exceptions import ForbiddenError, UserDoesNotExistsError
from fastapi import FastAPI
from fastapi.testclient import TestClient
from presentation.api.v1 import dependencies as deps
from presentation.api.v1.endpoints import user as user_endpoints


class DummySession:
    def __init__(self):
        self.commit = AsyncMock()
        self.rollback = AsyncMock()


def _current_user() -> User:
    return User(
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


def _build_user_app(use_case_overrides: dict):
    app = FastAPI()
    app.include_router(user_endpoints.router, prefix="/api/v1")
    session = DummySession()
    current_user = _current_user()

    async def override_db_session():
        yield session

    app.dependency_overrides[user_endpoints.get_db_session] = override_db_session
    app.dependency_overrides[deps.get_current_user] = lambda: current_user
    app.dependency_overrides.update(use_case_overrides)
    return app, session, current_user


def test_get_me_success():
    current_user = _current_user()
    use_case = AsyncMock()
    use_case.execute.return_value = current_user
    app, _session, _ = _build_user_app({deps.get_user_by_id_use_case: lambda: use_case})

    client = TestClient(app)
    response = client.get("/api/v1/users/me")

    assert response.status_code == 200
    assert response.json()["id"] == str(current_user.id)


def test_get_me_not_found_returns_404():
    use_case = AsyncMock()
    use_case.execute.side_effect = UserDoesNotExistsError("missing")
    app, _session, _ = _build_user_app({deps.get_user_by_id_use_case: lambda: use_case})

    client = TestClient(app)
    response = client.get("/api/v1/users/me")

    assert response.status_code == 404


def test_update_me_success_commits():
    current_user = _current_user()
    use_case = AsyncMock()
    use_case.execute.return_value = current_user
    app, session, _ = _build_user_app({deps.get_update_user_use_case: lambda: use_case})

    client = TestClient(app)
    response = client.patch("/api/v1/users/me", json={"name": "Jane"})

    assert response.status_code == 200
    session.commit.assert_awaited_once()


def test_get_user_by_id_forbidden_returns_403():
    use_case = AsyncMock()
    use_case.execute.side_effect = ForbiddenError("forbidden")
    app, _session, _ = _build_user_app({deps.get_user_by_id_use_case: lambda: use_case})

    client = TestClient(app)
    response = client.get(f"/api/v1/users/{uuid4()}")

    assert response.status_code == 403


def test_get_users_success():
    use_case = AsyncMock()
    use_case.execute.return_value = {"items": [], "total": 0, "page": 1, "limit": 30, "pages": 0}
    app, _session, _ = _build_user_app({deps.get_users_list_use_case: lambda: use_case})

    client = TestClient(app)
    response = client.get("/api/v1/users")

    assert response.status_code == 200
    assert response.json()["total"] == 0


def test_avatar_upload_url_rejects_wrong_content_type():
    use_case = AsyncMock()
    app, _session, _ = _build_user_app({deps.get_initiate_avatar_upload_use_case: lambda: use_case})
    client = TestClient(app)

    response = client.post(
        "/api/v1/users/me/avatar/upload-url",
        json={"filename": "avatar.bmp", "content_type": "image/bmp"},
    )

    assert response.status_code == 400
    use_case.execute.assert_not_called()


def test_avatar_upload_url_success():
    use_case = AsyncMock()
    use_case.execute.return_value = {"upload_url": "https://upload", "object_key": "avatars/path.png"}
    app, _session, _ = _build_user_app({deps.get_initiate_avatar_upload_use_case: lambda: use_case})
    client = TestClient(app)

    response = client.post(
        "/api/v1/users/me/avatar/upload-url",
        json={"filename": "avatar.png", "content_type": "image/png"},
    )

    assert response.status_code == 200
    assert response.json()["upload_url"] == "https://upload"


def test_confirm_avatar_upload_rejects_invalid_object_key():
    use_case = AsyncMock()
    app, _session, _ = _build_user_app({deps.get_update_user_use_case: lambda: use_case})
    client = TestClient(app)

    response = client.post("/api/v1/users/me/avatar/confirm?object_key=avatars/another-user/file.png")

    assert response.status_code == 403
