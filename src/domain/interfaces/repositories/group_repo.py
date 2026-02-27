from abc import ABC, abstractmethod
from uuid import UUID

from domain.entities import Group


class IGroupRepository(ABC):
    @abstractmethod
    async def create(self, group: Group) -> Group:
        pass

    @abstractmethod
    async def get_by_id(self, group_id: UUID) -> Group | None:
        pass

    @abstractmethod
    async def update(self, group: Group) -> Group:
        pass

    @abstractmethod
    async def delete(self, group_id: UUID) -> None:
        pass

    @abstractmethod
    async def get_all(self) -> list[Group]:
        pass
