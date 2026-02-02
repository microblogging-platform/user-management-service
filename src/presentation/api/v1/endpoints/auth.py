from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from domain.interfaces.security import IPasswordHasher
from infrastructure.db import get_db_session
from domain.entities import User
from domain.enums import Role
from domain.interfaces.repositories import IUserRepository
from presentation.api.v1.schemas.auth import SignupRequest, SignupResponse
from presentation.api.v1.dependencies import get_user_repository, get_password_hasher

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=SignupResponse, status_code=status.HTTP_201_CREATED)
async def signup(
    request: SignupRequest,
    user_repo: Annotated[IUserRepository, Depends(get_user_repository)],
    password_hasher: Annotated[IPasswordHasher, Depends(get_password_hasher)],
    session: Annotated[AsyncSession, Depends(get_db_session)]
) -> SignupResponse:

    if await user_repo.exists_by_username(request.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    
    if await user_repo.exists_by_email(request.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists"
        )
    
    try:
        password_hash = password_hasher.hash(request.password)
    except DomainValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    user = User(
        name=request.name,
        surname=request.surname,
        username=request.username,
        password_hash=password_hash,
        email=request.email,
        phone_number=request.phone_number,
        role=Role.USER,
        image_s3_path="",
        is_blocked=False,
        group_id=None
    )
    
    try:
        created_user = await user_repo.create(user)
        await session.commit()
        
        return SignupResponse(
            id=created_user.id,
            name=created_user.name,
            surname=created_user.surname,
            username=created_user.username,
            email=created_user.email,
            phone_number=str(created_user.phone_number),
            role=created_user.role.value
        )
    except DomainValidationError as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )
