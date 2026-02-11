from unittest.mock import AsyncMock

from application.dto.auth import TokenResponse
from domain.exceptions import InvalidCredentialsError, InvalidTokenError, UserAlreadyExistsError
from fastapi import FastAPI
from fastapi.testclient import TestClient
from presentation.api.v1 import dependencies as deps
from presentation.api.v1.endpoints import auth


class DummySession:
    def __init__(self):
        self.commit = AsyncMock()
        self.rollback = AsyncMock()


def _build_auth_app(use_case_overrides: dict):
    app = FastAPI()
    app.include_router(auth.router, prefix="/api/v1")
    session = DummySession()

    async def override_db_session():
        yield session

    app.dependency_overrides[auth.get_db_session] = override_db_session
    app.dependency_overrides.update(use_case_overrides)
    return app, session


def test_signup_success_commits_transaction():
    use_case = AsyncMock()
    app, session = _build_auth_app({deps.get_register_user_use_case: lambda: use_case})

    client = TestClient(app)
    response = client.post(
        "/api/v1/auth/signup",
        json={
            "name": "John",
            "surname": "Doe",
            "username": "johnny",
            "password": "secret123",
            "email": "john@example.com",
            "phone_number": "+14155552671",
        },
    )

    assert response.status_code == 201
    session.commit.assert_awaited_once()


def test_signup_duplicate_user_returns_conflict():
    use_case = AsyncMock()
    use_case.execute.side_effect = UserAlreadyExistsError("already exists")
    app, session = _build_auth_app({deps.get_register_user_use_case: lambda: use_case})

    client = TestClient(app)
    response = client.post(
        "/api/v1/auth/signup",
        json={
            "name": "John",
            "surname": "Doe",
            "username": "johnny",
            "password": "secret123",
            "email": "john@example.com",
            "phone_number": "+14155552671",
        },
    )

    assert response.status_code == 409
    session.rollback.assert_awaited_once()


def test_login_success_returns_tokens():
    use_case = AsyncMock()
    use_case.execute.return_value = TokenResponse(access_token="a", refresh_token="r")
    app, _session = _build_auth_app({deps.get_login_use_case: lambda: use_case})

    client = TestClient(app)
    response = client.post("/api/v1/auth/login", data={"username": "john", "password": "secret"})

    assert response.status_code == 200
    assert response.json()["access_token"] == "a"


def test_login_invalid_credentials_returns_401():
    use_case = AsyncMock()
    use_case.execute.side_effect = InvalidCredentialsError("bad credentials")
    app, session = _build_auth_app({deps.get_login_use_case: lambda: use_case})

    client = TestClient(app)
    response = client.post("/api/v1/auth/login", data={"username": "john", "password": "wrong"})

    assert response.status_code == 401
    session.rollback.assert_awaited_once()


def test_refresh_token_invalid_returns_401():
    use_case = AsyncMock()
    use_case.execute.side_effect = InvalidTokenError("invalid")
    app, session = _build_auth_app({deps.get_refresh_token_use_case: lambda: use_case})

    client = TestClient(app)
    response = client.post("/api/v1/auth/refresh-token", json={"refresh_token": "bad"})

    assert response.status_code == 401
    session.rollback.assert_awaited_once()


def test_reset_password_success():
    use_case = AsyncMock()
    app, session = _build_auth_app({deps.get_reset_password_use_case: lambda: use_case})

    client = TestClient(app)
    response = client.post("/api/v1/auth/reset-password", json={"token": "abc", "new_password": "newsecret12"})

    assert response.status_code == 200
    session.commit.assert_awaited_once()


def test_request_password_reset_always_200_when_ok():
    use_case = AsyncMock()
    app, _session = _build_auth_app({deps.get_request_password_reset_use_case: lambda: use_case})

    client = TestClient(app)
    response = client.post("/api/v1/auth/request-password-reset", json={"login": "john@example.com"})

    assert response.status_code == 200
    assert "reset link has been sent" in response.json()["detail"]
