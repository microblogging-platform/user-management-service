import pytest
from uuid import uuid4
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from domain.entities import User
from infrastructure.db.repositories.user_repo import SqlAlchemyUserRepository
from infrastructure.db.models.user import UserModel


def build_user_entity(**overrides) -> User:
    default = {
        "id": uuid4(),
        "name": "John",
        "surname": "Doe",
        "username": f"user_{uuid4().hex[:8]}",
        "password_hash": "secret_hash",
        "email": f"john_{uuid4().hex[:8]}@example.com",
        "phone_number": "+14155552671",
        "role": "USER",
        "image_s3_path": "",
        "is_blocked": False,
        "group_id": None,
    }
    default.update(overrides)
    return User(**default)


@pytest.mark.asyncio(loop_scope="session")
async def test_repo_create_and_get_by_id(db_session):
    repo = SqlAlchemyUserRepository(db_session)
    user_entity = build_user_entity(name="Alice")

    created_user = await repo.create(user_entity)

    assert created_user.id == user_entity.id
    assert created_user.name == "Alice"

    stmt = select(UserModel).where(UserModel.id == user_entity.id)
    result = await db_session.execute(stmt)
    user_in_db = result.scalar_one_or_none()

    assert user_in_db is not None
    assert user_in_db.username == user_entity.username

    fetched_user = await repo.get_by_id(user_entity.id)
    assert fetched_user == created_user


@pytest.mark.asyncio(loop_scope="session")
async def test_repo_create_duplicate_raises_error(db_session):
    repo = SqlAlchemyUserRepository(db_session)
    user1 = build_user_entity(username="same_login")
    user2 = build_user_entity(username="same_login")

    await repo.create(user1)

    with pytest.raises(IntegrityError):
        await repo.create(user2)


@pytest.mark.asyncio(loop_scope="session")
async def test_repo_update_user(db_session):
    repo = SqlAlchemyUserRepository(db_session)
    user = build_user_entity(name="Old Name")
    await repo.create(user)

    user.name = "New Name"

    updated_user = await repo.update(user)

    assert updated_user.name == "New Name"

    stmt = select(UserModel.name).where(UserModel.id == user.id)
    name_in_db = (await db_session.execute(stmt)).scalar()
    assert name_in_db == "New Name"


@pytest.mark.asyncio(loop_scope="session")
async def test_repo_delete_user(db_session):
    repo = SqlAlchemyUserRepository(db_session)
    user = build_user_entity()
    await repo.create(user)

    assert await repo.exists_by_id(user.id) is True

    await repo.delete(user.id)

    assert await repo.exists_by_id(user.id) is False

    stmt = select(UserModel).where(UserModel.id == user.id)
    result = await db_session.execute(stmt)
    assert result.scalar_one_or_none() is None


@pytest.mark.asyncio(loop_scope="session")
async def test_repo_update_password(db_session):
    repo = SqlAlchemyUserRepository(db_session)
    user = build_user_entity(password_hash="old_hash")
    await repo.create(user)

    await repo.update_password(user.id, "new_secure_hash")

    stmt = select(UserModel.password_hash).where(UserModel.id == user.id)
    new_hash = (await db_session.execute(stmt)).scalar()
    assert new_hash == "new_secure_hash"


@pytest.mark.asyncio(loop_scope="session")
async def test_repo_get_by_filters_and_pagination(db_session):
    repo = SqlAlchemyUserRepository(db_session)

    users_data = [
        ("Alice", "alice_user"),
        ("Bob", "bob_admin"),
        ("Charlie", "charlie_user"),
    ]

    for name, username in users_data:
        u = build_user_entity(name=name, username=username)
        await repo.create(u)

    found_bob = await repo.get_by_username("bob_admin")
    assert found_bob is not None
    assert found_bob.name == "Bob"

    results, total = await repo.get_all(limit=2, offset=0, sort_by="name", order_by="asc")

    assert total == 3
    assert len(results) == 2
    assert results[0].name == "Alice"
    assert results[1].name == "Bob"

    results_page_2, _ = await repo.get_all(limit=2, offset=2, sort_by="name", order_by="asc")
    assert len(results_page_2) == 1
    assert results_page_2[0].name == "Charlie"
