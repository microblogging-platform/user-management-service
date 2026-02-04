import logging
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Annotated

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from application.dto.user import UserDTO
from application.dto.user import UpdateUserCommand
from application.usecases.base import UseCase
from domain.entities import User
from domain.exceptions import UserDoesNotExistsError, UserBlockedError, UserAlreadyExistsError, DomainError, \
    ForbiddenError
from infrastructure.db import get_db_session
from infrastructure.db.models import UserModel
from presentation.api.v1.dependencies import get_current_user_use_case, get_current_user_id, get_update_user_use_case, \
    get_delete_user_use_case, get_current_user, get_user_by_id_use_case
from presentation.api.v1.schemas.user import UpdateUserRequest, UserResponse

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/me", response_model=UserDTO)
async def get_me(
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    use_case: Annotated[UseCase, Depends(get_current_user_use_case)],
):
    try:
        return await use_case.execute(user_id)

    except UserDoesNotExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message
        ) from e

    except UserBlockedError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=e.message
        ) from e

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        ) from e


@router.patch("/me", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def update_me(
        request: UpdateUserRequest,
        user_id: Annotated[UUID, Depends(get_current_user_id)],
        use_case: Annotated[UseCase, Depends(get_update_user_use_case)],
        session: Annotated[AsyncSession, Depends(get_db_session)],
):
    command = UpdateUserCommand(**request.model_dump(exclude_unset=True))

    try:
        user_dto = await use_case.execute(user_id, command)

        await session.commit()

        return UserResponse.model_validate(user_dto)

    except UserAlreadyExistsError as e:
        await session.rollback()
        logging.error(f"Error updating profile: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=e.message)
    except DomainError as e:
        await session.rollback()
        logging.error(f"Error updating profile: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except Exception as e:
        await session.rollback()
        logging.error(f"Error updating profile: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update profile")


@router.delete("/me", status_code=status.HTTP_200_OK)
async def delete_me(
        user_id: Annotated[UUID, Depends(get_current_user_id)],
        use_case: Annotated[UseCase, Depends(get_delete_user_use_case)],
        session: Annotated[AsyncSession, Depends(get_db_session)],
):

    try:
        await use_case.execute(user_id)
        await session.commit()

    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete user")


@router.get("/{user_id}", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def get_user_by_id(
        user_id: UUID,
        current_user: Annotated[User, Depends(get_current_user)],
        use_case: Annotated[UseCase, Depends(get_user_by_id_use_case)],
):
    try:
        user_dto =  await use_case.execute(user_id, current_user)

        return UserResponse.model_validate(user_dto)

    except ForbiddenError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=e.message
        )
    except UserDoesNotExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message
        )


@router.get("", response_model=list[UserResponse], status_code=status.HTTP_200_OK)
async def get_users(
        session: Annotated[AsyncSession, Depends(get_db_session)],
):
    stmt = select(UserModel)
    result = await session.execute(stmt)
    return result.scalars().all()