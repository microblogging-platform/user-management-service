import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

from domain.entities import User
from infrastructure.db.repositories.user_repo import SqlAlchemyUserRepository


def run(coro):
    return asyncio.run(coro)


def build_user() -> User:
    return User(
        id=uuid4(),
        name="John",
        surname="Doe",
        username="johnny",
        password_hash="hash",
        email="john@example.com",
        phone_number="+14155552671",
        role="USER",
        image_s3_path="",
        is_blocked=False,
        group_id=None,
    )


def test_user_repository_create_and_get():
    session = Mock()
    session.flush = AsyncMock()
    session.refresh = AsyncMock()
    session.execute = AsyncMock()
    session.add = Mock()
    repo = SqlAlchemyUserRepository(session)
    user = build_user()
    model = SimpleNamespace()

    repo._mapper = Mock()
    repo._mapper.to_model.return_value = model
    repo._mapper.to_domain.return_value = user

    created = run(repo.create(user))
    assert created == user

    result_obj = Mock()
    result_obj.scalar_one_or_none.return_value = model
    session.execute.return_value = result_obj

    fetched = run(repo.get_by_id(user.id))
    assert fetched == user


def test_user_repository_update_password_delete_and_exists():
    session = Mock()
    session.flush = AsyncMock()
    session.execute = AsyncMock()
    session.delete = AsyncMock()
    repo = SqlAlchemyUserRepository(session)
    user = build_user()
    model = SimpleNamespace(**user.model_dump())

    result_for_update = Mock()
    result_for_update.scalar_one.return_value = model
    result_for_delete = Mock()
    result_for_delete.scalar_one_or_none.return_value = model
    result_for_exists = Mock()
    result_for_exists.scalar.return_value = True
    session.execute.side_effect = [
        result_for_update,
        Mock(),
        result_for_delete,
        result_for_exists,
        result_for_exists,
        result_for_exists,
    ]

    updated_user = build_user()
    updated = run(repo.update(updated_user))
    assert isinstance(updated, User)

    run(repo.update_password(updated_user.id, "new-hash"))
    run(repo.delete(updated_user.id))
    assert run(repo.exists_by_username("john")) is True
    assert run(repo.exists_by_email("john@example.com")) is True
    assert run(repo.exists_by_id(updated_user.id)) is True


def test_user_repository_get_all_and_getters(monkeypatch):
    session = AsyncMock()
    repo = SqlAlchemyUserRepository(session)
    user_model = SimpleNamespace(id=uuid4())
    user = build_user()

    result_one = Mock()
    result_one.scalar_one_or_none.return_value = user_model
    result_two = Mock()
    result_two.scalar_one_or_none.return_value = user_model
    total_result = Mock()
    total_result.scalar_one.return_value = 1
    users_result = Mock()
    users_result.scalars.return_value.all.return_value = [user_model]
    session.execute.side_effect = [result_one, result_two, total_result, users_result]

    mapper_mock = Mock()
    mapper_mock.to_domain.return_value = user
    repo._mapper = mapper_mock
    monkeypatch.setattr("infrastructure.db.repositories.user_repo.user_mapper", mapper_mock)

    assert run(repo.get_by_username("john")) == user
    assert run(repo.get_by_email("john@example.com")) == user
    users, total = run(repo.get_all(limit=10, offset=0, filter_by_name="jo", sort_by="username", order_by="desc"))
    assert total == 1
    assert users[0] == user
