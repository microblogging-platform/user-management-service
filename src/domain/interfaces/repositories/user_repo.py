from abc import ABC, abstractmethod
from uuid import UUID
from typing import Optional, List, Protocol
from pydantic import EmailStr
from domain.entities import User

class IUserRepository(Protocol):

    @abstractmethod
    async def create(self, user: User) -> User:
        pass

    @abstractmethod
    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        pass

    @abstractmethod
    async def get_by_username(self, username: str) -> Optional[User]:
        pass

    @abstractmethod
    async def get_by_email(self, email: EmailStr) -> Optional[User]:
        pass

    @abstractmethod
    async def get_by_group_id(self, group_id: UUID) -> List[User]:
        pass

    @abstractmethod
    async def update(self, user: User) -> User:
        pass

    @abstractmethod
    async def delete(self, user_id: UUID) -> None:
        pass

    @abstractmethod
    async def exists_by_username(self, username: str) -> bool:
        pass

    @abstractmethod
    async def exists_by_email(self, email: EmailStr) -> bool:
        pass