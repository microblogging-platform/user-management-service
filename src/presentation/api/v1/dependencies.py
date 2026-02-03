from typing import Annotated

from application.usecases.auth.login_user import LoginUserUseCase
from application.usecases.auth.refresh_token import RefreshTokenUseCase
from application.usecases.auth.register_user import RegisterUserUseCase
from application.usecases.base import UseCase
from domain.interfaces.repositories import IGroupRepository, IUserRepository
from domain.interfaces.security import IPasswordHasher, ITokenService
from fastapi import Depends
from infrastructure.db import get_db_session
from infrastructure.db.repositories import (
    SqlAlchemyGroupRepository,
    SqlAlchemyUserRepository,
)
from infrastructure.security import Argon2Hasher
from infrastructure.security.jwt_service import PyJWTService
from sqlalchemy.ext.asyncio import AsyncSession

def get_password_hasher() -> IPasswordHasher:
    return Argon2Hasher()


def get_jwt_service() -> ITokenService:
    return PyJWTService()


async def get_user_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> IUserRepository:
    return SqlAlchemyUserRepository(session)


async def get_group_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> IGroupRepository:
    return SqlAlchemyGroupRepository(session)


async def get_register_user_use_case(
    user_repo: Annotated[IUserRepository, Depends(get_user_repository)],
    password_hasher: Annotated[IPasswordHasher, Depends(get_password_hasher)],
) -> UseCase:
    return RegisterUserUseCase(user_repo, password_hasher)


async def get_login_use_case(
    user_repo: Annotated[IUserRepository, Depends(get_user_repository)],
    password_hasher: Annotated[IPasswordHasher, Depends(get_password_hasher)],
    token_service: Annotated[ITokenService, Depends(get_jwt_service)],
) -> UseCase:
    return LoginUserUseCase(user_repo, password_hasher, token_service)

async def get_refresh_token_use_case(
    user_repo: Annotated[IUserRepository, Depends(get_user_repository)],
    token_service: Annotated[ITokenService, Depends(get_jwt_service)],
) -> UseCase:
    return RefreshTokenUseCase(user_repo, token_service)
