from uuid import uuid4

import pytest
from sqlalchemy import select

from domain.entities import Group
from infrastructure.db.models.group import GroupModel
from infrastructure.db.repositories.group_repo import SqlAlchemyGroupRepository


def build_group_entity(**overrides) -> Group:
    default = {"id": uuid4(), "name": f"group_{uuid4().hex[:8]}"}
    default.update(overrides)
    return Group(**default)


@pytest.mark.asyncio(loop_scope="session")
async def test_group_repository_crud(db_session):
    repo = SqlAlchemyGroupRepository(db_session)
    group = build_group_entity(name="mods")

    created = await repo.create(group)
    assert created.id == group.id
    assert created.name == "mods"

    fetched = await repo.get_by_id(group.id)
    assert fetched is not None
    assert fetched.name == "mods"

    group.name = "admins"
    updated = await repo.update(group)
    assert updated.name == "admins"

    stmt = select(GroupModel.name).where(GroupModel.id == group.id)
    name_in_db = (await db_session.execute(stmt)).scalar()
    assert name_in_db == "admins"

    groups = await repo.get_all()
    assert len(groups) >= 1
    assert any(g.id == group.id for g in groups)

    await repo.delete(group.id)
    assert await repo.get_by_id(group.id) is None


@pytest.mark.asyncio(loop_scope="session")
async def test_group_repository_update_missing_group_raises(db_session):
    repo = SqlAlchemyGroupRepository(db_session)
    missing_group = build_group_entity(name="missing")

    with pytest.raises(ValueError):
        await repo.update(missing_group)
