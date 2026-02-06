from typing import Annotated
from uuid import UUID

from fastapi.security import OAuth2PasswordBearer
from starlette import status

from application.usecases.auth.login_user import LoginUserUseCase
from application.usecases.auth.refresh_token import RefreshTokenUseCase
from application.usecases.auth.register_user import RegisterUserUseCase
from application.usecases.base import UseCase
from application.usecases.users.delete_user import DeleteUserUseCase
from application.usecases.users.get_current_user import GetCurrentUserUseCase
from application.usecases.users.get_user import GetUserByIdUseCase
from application.usecases.users.get_users import GetUsersUseCase
from application.usecases.users.initiate_avatar_upload import InitiateAvatarUploadUseCase
from application.usecases.users.update_user import UpdateUserUseCase
from domain.entities import User
from domain.exceptions import InvalidTokenError, ExpiredTokenError
from domain.interfaces.repositories import IGroupRepository, IUserRepository
from domain.interfaces.security import IPasswordHasher, ITokenService
from fastapi import Depends, HTTPException

from domain.interfaces.services.storage import IStorageService
from infrastructure.db import get_db_session
from infrastructure.db.repositories import (
    SqlAlchemyGroupRepository,
    SqlAlchemyUserRepository,
)
from infrastructure.security import Argon2Hasher
from infrastructure.security.jwt_service import PyJWTService
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.services.s3_service import S3Service

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")

def get_password_hasher() -> IPasswordHasher:
    return Argon2Hasher()

def get_jwt_service() -> ITokenService:
    return PyJWTService()

async def get_user_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> IUserRepository:
    return SqlAlchemyUserRepository(session)

async def get_current_user_id(
        token: Annotated[str, Depends(oauth2_scheme)],
        token_service: Annotated[ITokenService, Depends(get_jwt_service)],
) -> UUID:
    try:
        return token_service.get_user_id_from_token(token)

    except (InvalidTokenError, ExpiredTokenError) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=e.message,
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_user(
        user_id: Annotated[UUID, Depends(get_current_user_id)],

        user_repo: Annotated[IUserRepository, Depends(get_user_repository)],
) -> User:
    user = await user_repo.get_by_id(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if user.is_blocked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is blocked",
        )

    return user

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

async def get_current_user_use_case(
    user_repo: Annotated[IUserRepository, Depends(get_user_repository)],
) -> UseCase:
    return GetCurrentUserUseCase(user_repo)

async def get_update_user_use_case(
    user_repo: Annotated[IUserRepository, Depends(get_user_repository)],
) -> UseCase:
    return UpdateUserUseCase(user_repo)

async def get_delete_user_use_case(
    user_repo: Annotated[IUserRepository, Depends(get_user_repository)],
) -> UseCase:
    return DeleteUserUseCase(user_repo)

async def get_user_by_id_use_case(
    user_repo: Annotated[IUserRepository, Depends(get_user_repository)],
) -> UseCase:
    return GetUserByIdUseCase(user_repo)

async def get_users_list_use_case(
    user_repo: Annotated[IUserRepository, Depends(get_user_repository)],
) -> UseCase:
    return GetUsersUseCase(user_repo)

async def get_storage_service() -> IStorageService:
    return S3Service()

async def get_initiate_avatar_upload_use_case(
    storage_service: Annotated[IStorageService, Depends(get_storage_service)],
) -> UseCase:
    return InitiateAvatarUploadUseCase(storage_service)