from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from domain.entities import Group
from domain.interfaces.repositories import IGroupRepository
from infrastructure.db.mappers import group_mapper
from infrastructure.db.models import GroupModel


class SqlAlchemyGroupRepository(IGroupRepository):
    def __init__(self, session: AsyncSession):
        self._session = session
        self._mapper = group_mapper

    async def create(self, group: Group) -> Group:
        group_model = self._mapper.to_model(group)
        self._session.add(group_model)
        await self._session.flush()
        await self._session.refresh(group_model)
        return self._mapper.to_domain(group_model)

    async def get_by_id(self, group_id: UUID) -> Optional[Group]:
        stmt = select(GroupModel).where(GroupModel.id == group_id)
        result = await self._session.execute(stmt)
        group_model = result.scalar_one_or_none()
        return self._mapper.to_domain(group_model) if group_model else None

    async def update(self, group: Group) -> Group:
        stmt = select(GroupModel).where(GroupModel.id == group.id)
        result = await self._session.execute(stmt)
        group_model = result.scalar_one_or_none()

        if not group_model:
            raise ValueError(f"Group with id {group.id} not found")

        group_model.name = group.name

        await self._session.flush()
        await self._session.refresh(group_model)
        return self._mapper.to_domain(group_model)

    async def delete(self, group_id: UUID) -> None:
        stmt = select(GroupModel).where(GroupModel.id == group_id)
        result = await self._session.execute(stmt)
        group_model = result.scalar_one_or_none()

        if group_model:
            await self._session.delete(group_model)
            await self._session.flush()

    async def get_all(self) -> List[Group]:
        stmt = select(GroupModel)
        result = await self._session.execute(stmt)
        group_models = result.scalars().all()
        return [self._mapper.to_domain(model) for model in group_models]
