from unittest.mock import AsyncMock, Mock

import pytest

from application.dto.auth import LoginCommand, RegisterUserCommand
from application.usecases.auth.login_user import LoginUserUseCase
from application.usecases.auth.refresh_token import RefreshTokenUseCase
from application.usecases.auth.register_user import RegisterUserUseCase
from application.usecases.auth.request_password_reset import RequestPasswordResetUseCase
from application.usecases.auth.reset_password import ResetPasswordUseCase
from domain.entities import User
from domain.exceptions import InvalidCredentialsError, InvalidTokenError, UserAlreadyExistsError, UserBlockedError


@pytest.mark.asyncio
async def test_login_user_success(user_kwargs):
    user = User(**user_kwargs)
    repo = AsyncMock()
    repo.get_by_login_identifier.return_value = user

    hasher = AsyncMock()
    hasher.verify.return_value = True
    tokens = Mock()
    tokens.create_access_token.return_value = "access"
    tokens.create_refresh_token.return_value = "refresh"

    result = await LoginUserUseCase(repo, hasher, tokens).execute(LoginCommand(login="johnny", password="secret"))

    assert result.access_token == "access"
    assert result.refresh_token == "refresh"


@pytest.mark.asyncio
async def test_login_user_invalid_login():
    repo = AsyncMock()
    repo.get_by_login_identifier.return_value = None
    hasher = AsyncMock()
    tokens = Mock()

    with pytest.raises(InvalidCredentialsError):
        await LoginUserUseCase(repo, hasher, tokens).execute(LoginCommand(login="missing", password="secret"))


@pytest.mark.asyncio
async def test_login_user_blocked(user_kwargs):
    user = User(**{**user_kwargs, "is_blocked": True})
    repo = AsyncMock()
    repo.get_by_login_identifier.return_value = user
    hasher = AsyncMock()
    hasher.verify.return_value = True
    tokens = Mock()

    with pytest.raises(UserBlockedError):
        await LoginUserUseCase(repo, hasher, tokens).execute(LoginCommand(login="johnny", password="secret"))


@pytest.mark.asyncio
async def test_register_user_duplicate_username(user_kwargs):
    repo = AsyncMock()
    repo.exists_by_username.return_value = True
    repo.exists_by_email.return_value = False
    hasher = Mock()

    command = RegisterUserCommand(
        name=user_kwargs["name"],
        surname=user_kwargs["surname"],
        username=user_kwargs["username"],
        password="secret123",
        email=user_kwargs["email"],
        phone_number=user_kwargs["phone_number"],
    )

    with pytest.raises(UserAlreadyExistsError):
        await RegisterUserUseCase(repo, hasher).execute(command)


@pytest.mark.asyncio
async def test_register_user_success(user_kwargs):
    repo = AsyncMock()
    repo.exists_by_username.return_value = False
    repo.exists_by_email.return_value = False
    hasher = AsyncMock()
    hasher.hash.return_value = "hashed!"

    command = RegisterUserCommand(
        name=user_kwargs["name"],
        surname=user_kwargs["surname"],
        username=user_kwargs["username"],
        password="secret123",
        email=user_kwargs["email"],
        phone_number=user_kwargs["phone_number"],
    )

    await RegisterUserUseCase(repo, hasher).execute(command)

    repo.create.assert_awaited_once()

    created_user = repo.create.await_args.args[0]
    assert created_user.password_hash == "hashed!"


@pytest.mark.asyncio
async def test_refresh_token_blacklisted():
    repo = AsyncMock()
    token_service = Mock()
    blacklist = AsyncMock()
    blacklist.is_blacklisted.return_value = True

    with pytest.raises(InvalidTokenError):
        await RefreshTokenUseCase(repo, token_service, blacklist).execute("bad-token")


@pytest.mark.asyncio
async def test_refresh_token_success(user_kwargs):
    user = User(**user_kwargs)
    repo = AsyncMock()
    repo.get_by_id.return_value = user

    token_service = Mock()
    token_service.decode_token.return_value = {"sub": user.id, "type": "refresh", "exp": 12345}
    token_service.create_access_token.return_value = "new-access"
    token_service.create_refresh_token.return_value = "new-refresh"

    blacklist = AsyncMock()
    blacklist.is_blacklisted.return_value = False

    result = await RefreshTokenUseCase(repo, token_service, blacklist).execute("refresh-token")

    assert result.access_token == "new-access"
    assert result.refresh_token == "new-refresh"

    blacklist.blacklist_token.assert_awaited_once_with("refresh-token", expires_at=12345)


@pytest.mark.asyncio
async def test_request_password_reset_when_user_missing():
    repo = AsyncMock()
    repo.get_by_login_identifier.return_value = None
    token_service = Mock()
    broker = AsyncMock()

    await RequestPasswordResetUseCase(repo, token_service, broker).execute("missing@example.com")

    broker.publish.assert_not_called()


@pytest.mark.asyncio
async def test_request_password_reset_publish_event(user_kwargs):
    user = User(**user_kwargs)
    repo = AsyncMock()
    repo.get_by_login_identifier.return_value = user
    token_service = Mock()
    token_service.create_reset_token.return_value = "reset-token"
    broker = AsyncMock()

    await RequestPasswordResetUseCase(repo, token_service, broker).execute(user.username)

    broker.publish.assert_awaited_once()

    kwargs = broker.publish.await_args.kwargs
    assert kwargs["queue_name"] == "reset-password-stream"
    assert kwargs["message"]["payload"]["recipient_email"] == user.email


@pytest.mark.asyncio
async def test_reset_password_invalid_token():
    repo = AsyncMock()
    token_service = Mock()
    token_service.decode_token.side_effect = RuntimeError("decode error")
    hasher = AsyncMock()
    blacklist = AsyncMock()
    blacklist.is_blacklisted.return_value = False

    with pytest.raises(InvalidTokenError):
        await ResetPasswordUseCase(repo, token_service, hasher, blacklist).execute("bad", "new-secret")


@pytest.mark.asyncio
async def test_reset_password_success(user_kwargs):
    user = User(**user_kwargs)
    repo = AsyncMock()
    repo.exists_by_id.return_value = True

    token_service = Mock()
    token_service.decode_token.return_value = {"sub": user.id, "type": "reset_password", "exp": 999}

    hasher = AsyncMock()
    hasher.hash.return_value = "new-hash"

    blacklist = AsyncMock()
    blacklist.is_blacklisted.return_value = False

    await ResetPasswordUseCase(repo, token_service, hasher, blacklist).execute("reset-token", "new-secret")

    repo.update_password.assert_awaited_once_with(user.id, "new-hash")
    blacklist.blacklist_token.assert_awaited_once_with("reset-token", expires_at=999)
