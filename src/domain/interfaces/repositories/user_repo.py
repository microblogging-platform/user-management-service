from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from pydantic_extra_types.phone_numbers import PhoneNumber

from domain.entities import User
from pydantic import EmailStr


class IUserRepository(ABC):

    @abstractmethod
    async def create(self, user: User) -> User:
        pass

    @abstractmethod
    async def get_by_id(self, user_id: UUID) -> User | None:
        pass

    @abstractmethod
    async def get_by_login_identifier(self, identifier: str | EmailStr | PhoneNumber) -> User | None:
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

    @abstractmethod
    async def get_all(
            self,
            limit: int,
            offset: int,
            filter_by_name: str | None = None,
            sort_by: str | None = None,
            order_by: str = "asc",
            group_id: UUID | None = None
    ) -> tuple[list[User], int]:
        pass

