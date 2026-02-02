from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from passlib.context import CryptContext

from infrastructure.db import get_db_session
from infrastructure.db.repositories import SqlAlchemyUserRepository, SqlAlchemyGroupRepository
from domain.interfaces.repositories import IUserRepository, IGroupRepository

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


async def get_user_repository(session: Annotated[AsyncSession, Depends(get_db_session)]) -> IUserRepository:
    return SqlAlchemyUserRepository(session)


async def get_group_repository(session: Annotated[AsyncSession, Depends(get_db_session)]) -> IGroupRepository:
    return SqlAlchemyGroupRepository(session)

