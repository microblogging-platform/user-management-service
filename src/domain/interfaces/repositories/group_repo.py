from abc import abstractmethod, ABC
from uuid import UUID
from typing import Optional, List

from domain.entities import Group


class IGroupRepository(ABC):

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