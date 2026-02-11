import asyncio
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from application.dto.user import GetUsersQuery, UpdateUserCommand
from application.usecases.users.delete_user import DeleteUserUseCase
from application.usecases.users.get_user import GetUserByIdUseCase
from application.usecases.users.get_users import GetUsersUseCase
from application.usecases.users.initiate_avatar_upload import InitiateAvatarUploadUseCase
from application.usecases.users.update_user import UpdateUserUseCase
from domain.entities import User
from domain.enums import Role
from domain.exceptions import ForbiddenError, UserAlreadyExistsError, UserDoesNotExistsError


def run(coro):
    return asyncio.run(coro)


def test_get_user_by_id_not_found(user_kwargs):
    repo = AsyncMock()
    repo.get_by_id.return_value = None
    storage = AsyncMock()
    requester = User(**user_kwargs)

    with pytest.raises(UserDoesNotExistsError):
        run(GetUserByIdUseCase(repo, storage).execute(uuid4(), requester))


def test_get_user_by_id_allows_admin_and_builds_image_url(user_kwargs):
    target = User(**{**user_kwargs, "image_s3_path": "avatars/path.png"})
    requester = User(**{**user_kwargs, "id": uuid4(), "role": Role.ADMIN})
    repo = AsyncMock()
    repo.get_by_id.return_value = target
    storage = AsyncMock()
    storage.generate_presigned_get_url.return_value = "https://signed/url"

    result = run(GetUserByIdUseCase(repo, storage).execute(target.id, requester))

    assert result.image_s3_path == "https://signed/url"


def test_get_user_by_id_forbidden_for_unrelated_user(user_kwargs):
    target = User(**user_kwargs)
    requester = User(**{**user_kwargs, "id": uuid4(), "role": Role.USER})
    repo = AsyncMock()
    repo.get_by_id.return_value = target
    storage = AsyncMock()

    with pytest.raises(ForbiddenError):
        run(GetUserByIdUseCase(repo, storage).execute(target.id, requester))


def test_get_users_for_moderator_without_group_returns_empty(user_kwargs):
    requester = User(**{**user_kwargs, "role": Role.MODERATOR, "group_id": None})
    repo = AsyncMock()
    storage = AsyncMock()
    query = GetUsersQuery(page=1, limit=10)

    result = run(GetUsersUseCase(repo, storage).execute(query, requester))

    assert result.total == 0
    assert result.items == []


def test_get_users_for_admin_success(user_kwargs):
    requester = User(**{**user_kwargs, "role": Role.ADMIN})
    user = User(**{**user_kwargs, "image_s3_path": "avatars/avatar.png"})
    repo = AsyncMock()
    repo.get_all.return_value = ([user], 1)
    storage = AsyncMock()
    storage.generate_presigned_get_url.return_value = "https://signed/avatar"
    query = GetUsersQuery(page=1, limit=30, order_by="asc")

    result = run(GetUsersUseCase(repo, storage).execute(query, requester))

    assert result.total == 1
    assert result.pages == 1
    assert result.items[0].image_s3_path == "https://signed/avatar"


def test_get_users_for_basic_user_forbidden(user_kwargs):
    requester = User(**{**user_kwargs, "role": Role.USER})
    repo = AsyncMock()
    storage = AsyncMock()
    query = GetUsersQuery()

    with pytest.raises(ForbiddenError):
        run(GetUsersUseCase(repo, storage).execute(query, requester))


def test_update_user_rejects_duplicate_username(user_kwargs):
    user = User(**user_kwargs)
    requester = user
    repo = AsyncMock()
    repo.get_by_id.return_value = user
    repo.get_by_login_identifier.return_value = User(**{**user_kwargs, "id": uuid4()})
    command = UpdateUserCommand(username="taken")

    with pytest.raises(UserAlreadyExistsError):
        run(UpdateUserUseCase(repo).execute(user.id, command, requester))


def test_update_user_success(user_kwargs):
    user = User(**user_kwargs)
    requester = user
    repo = AsyncMock()
    repo.get_by_id.return_value = user
    repo.get_by_login_identifier.return_value = None
    repo.update.return_value = user
    command = UpdateUserCommand(name="Jane")

    result = run(UpdateUserUseCase(repo).execute(user.id, command, requester))

    assert result.name == "Jane"
    repo.update.assert_awaited_once()


def test_delete_user_use_case_returns_repository_result():
    repo = AsyncMock()
    repo.delete.return_value = None

    result = DeleteUserUseCase(repo).execute(uuid4())

    assert asyncio.iscoroutine(result)
    run(result)


def test_initiate_avatar_upload_use_case_returns_object_key(user_kwargs):
    storage = AsyncMock()
    storage.generate_presigned_upload_url.return_value = "https://upload"
    user_id = user_kwargs["id"]

    result = run(
        InitiateAvatarUploadUseCase(storage).execute(user_id=user_id, filename="avatar.png", content_type="image/png")
    )

    assert result.upload_url == "https://upload"
    assert result.object_key.startswith(f"avatars/{user_id}/")
    assert result.object_key.endswith(".png")
