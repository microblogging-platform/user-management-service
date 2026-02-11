import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from domain.entities import Group
from infrastructure.db.repositories.group_repo import SqlAlchemyGroupRepository


def run(coro):
    return asyncio.run(coro)


def test_group_repository_crud():
    session = Mock()
    session.flush = AsyncMock()
    session.refresh = AsyncMock()
    session.execute = AsyncMock()
    session.delete = AsyncMock()
    session.add = Mock()
    repo = SqlAlchemyGroupRepository(session)
    group = Group(id=uuid4(), name="mods")
    model = SimpleNamespace(id=group.id, name="mods")
    repo._mapper = Mock()
    repo._mapper.to_model.return_value = model
    repo._mapper.to_domain.side_effect = lambda obj: Group(id=obj.id, name=obj.name)

    created = run(repo.create(group))
    assert created.id == group.id
    assert created.name == group.name

    one = Mock()
    one.scalar_one_or_none.return_value = model
    all_result = Mock()
    all_result.scalars.return_value.all.return_value = [model]
    session.execute.side_effect = [one, one, one, all_result]

    loaded = run(repo.get_by_id(group.id))
    assert loaded is not None
    assert loaded.id == group.id
    assert loaded.name == group.name
    updated = run(repo.update(Group(id=group.id, name="admins")))
    assert updated.name == "admins"
    run(repo.delete(group.id))
    groups = run(repo.get_all())
    assert len(groups) == 1
    assert groups[0].id == group.id


def test_group_repository_update_missing_group_raises():
    session = AsyncMock()
    repo = SqlAlchemyGroupRepository(session)
    result = Mock()
    result.scalar_one_or_none.return_value = None
    session.execute.return_value = result

    with pytest.raises(ValueError):
        run(repo.update(Group(id=uuid4(), name="missing")))
