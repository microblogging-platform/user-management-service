from abc import ABC, abstractmethod
from uuid import UUID
from typing import Optional, List, Protocol

from ..entities.group import Group


class GroupRepository(Protocol):

    @abstractmethod
    async def create(self, group: Group) -> Group:
        pass

    @abstractmethod
    async def get_by_id(self, group_id: UUID) -> Optional[Group]:
        pass

    @abstractmethod
    async def update(self, group: Group) -> Group:
        pass

    @abstractmethod
    async def delete(self, group_id: UUID) -> None:
        pass

    @abstractmethod
    async def get_all(self) -> List[Group]:
        pass
