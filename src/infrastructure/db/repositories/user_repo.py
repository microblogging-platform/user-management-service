from typing import Optional, List
from uuid import UUID

from pydantic import EmailStr

from domain.entities import User
from domain.repositories import UserRepository


class SqlAlchemyUserRepository(UserRepository):
    async def create(self, user: User) -> User:
        pass

    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        pass

    async def get_by_username(self, username: str) -> Optional[User]:
        pass

    async def get_by_email(self, email: EmailStr) -> Optional[User]:
        pass

    async def get_by_group_id(self, group_id: UUID) -> List[User]:
        pass

    async def update(self, user: User) -> User:
        pass

    async def delete(self, user_id: UUID) -> None:
        pass

    async def exists_by_username(self, username: str) -> bool:
        pass

    async def exists_by_email(self, email: EmailStr) -> bool:
        pass