from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from infrastructure.db import get_db_session
from infrastructure.db.repositories import SqlAlchemyUserRepository, SqlAlchemyGroupRepository
from infrastructure.security import BcryptHasher
from infrastructure.security.jwt_service import PyJWTService
from domain.interfaces.repositories import IUserRepository, IGroupRepository
from domain.interfaces.security import IPasswordHasher, ITokenService

_password_hasher = BcryptHasher()
_jwt_service = PyJWTService()


def get_password_hasher() -> IPasswordHasher:
    return _password_hasher

def get_jwt_service() -> ITokenService:
    return _jwt_service


async def get_user_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)]
) -> IUserRepository:
    return SqlAlchemyUserRepository(session)


async def get_group_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)]
) -> IGroupRepository:
    return SqlAlchemyGroupRepository(session)

