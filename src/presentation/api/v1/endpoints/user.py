import logging
from typing import Annotated, Literal
from uuid import UUID

from application.dto.user import GetUsersQuery, UpdateUserCommand, UserDTO, UsersListResponse
from application.usecases.base import UseCase
from domain.entities import User
from domain.exceptions import (
    DomainError,
    ForbiddenError,
    UserAlreadyExistsError,
    UserBlockedError,
    UserDoesNotExistsError,
)
from fastapi import APIRouter, Depends, HTTPException, Query, status
from infrastructure.db import get_db_session
from presentation.api.v1.dependencies import (
    get_current_user,
    get_delete_user_use_case,
    get_initiate_avatar_upload_use_case,
    get_update_user_use_case,
    get_user_by_id_use_case,
    get_users_list_use_case,
)
from presentation.api.v1.schemas.user import (
    AvatarPresignedUrlResponse,
    AvatarUploadRequest,
    UpdateUserRequest,
    UserResponse,
)
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserDTO)
async def get_me(
    current_user: Annotated[User, Depends(get_current_user)],
    use_case: Annotated[UseCase, Depends(get_user_by_id_use_case)],
):
    try:
        user_dto = await use_case.execute(user_id=current_user.id, requester=current_user)

        return user_dto

    except UserDoesNotExistsError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message) from e

    except UserBlockedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=e.message) from e

    except Exception as e:
        logging.exception(e)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found") from e


@router.patch("/me", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def update_me(
    request: UpdateUserRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    use_case: Annotated[UseCase, Depends(get_update_user_use_case)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
):
    command = UpdateUserCommand(**request.model_dump(exclude_unset=True))

    try:
        user_dto = await use_case.execute(user_id=current_user.id, command=command, requester=current_user)

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
    user_id: Annotated[UUID, Depends(get_current_user)],
    use_case: Annotated[UseCase, Depends(get_delete_user_use_case)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
):

    try:
        await use_case.execute(user_id)
        await session.commit()

    except Exception:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete user")


@router.get("/{user_id}", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def get_user_by_id(
    user_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    use_case: Annotated[UseCase, Depends(get_user_by_id_use_case)],
):
    try:
        user_dto = await use_case.execute(user_id=user_id, requester=current_user)

        return UserResponse.model_validate(user_dto)

    except ForbiddenError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=e.message)
    except UserDoesNotExistsError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)


@router.patch("/{user_id}", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def update_user_by_id(
    user_id: UUID,
    request: UpdateUserRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    use_case: Annotated[UseCase, Depends(get_update_user_use_case)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
):
    command = UpdateUserCommand(**request.model_dump(exclude_unset=True))

    try:
        user_dto = await use_case.execute(user_id=user_id, command=command, requester=current_user)

        await session.commit()
        return user_dto

    except ForbiddenError as e:
        await session.rollback()
        raise HTTPException(status_code=403, detail=e.message)

    except UserDoesNotExistsError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)


@router.get("", response_model=UsersListResponse)
async def get_users(
    use_case: Annotated[UseCase, Depends(get_users_list_use_case)],
    current_user: Annotated[User, Depends(get_current_user)],
    page: int = Query(1, ge=1),
    limit: int = Query(30, ge=1, le=100),
    filter_by_name: str | None = Query(None),
    sort_by: str | None = Query(None),
    order_by: Literal["asc", "desc"] = Query("asc"),
):
    query = GetUsersQuery(page=page, limit=limit, filter_by_name=filter_by_name, sort_by=sort_by, order_by=order_by)

    try:
        return await use_case.execute(query, requester=current_user)

    except ForbiddenError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.post("/me/avatar/upload-url", response_model=AvatarPresignedUrlResponse)
async def get_avatar_upload_url(
    request: AvatarUploadRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    use_case: Annotated[UseCase, Depends(get_initiate_avatar_upload_use_case)],
):
    if request.content_type not in ["image/jpeg", "image/png", "image/webp"]:
        raise HTTPException(status_code=400, detail="Allowed formats: jpeg, png, webp")

    return await use_case.execute(user_id=current_user.id, filename=request.filename, content_type=request.content_type)


@router.post("/me/avatar/confirm", response_model=UserDTO)
async def confirm_avatar_upload(
    object_key: str,
    current_user: Annotated[User, Depends(get_current_user)],
    use_case: Annotated[UseCase, Depends(get_update_user_use_case)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
):
    expected_prefix = f"avatars/{current_user.id}/"
    if not object_key.startswith(expected_prefix):
        raise HTTPException(status_code=403, detail="Invalid object key")

    command = UpdateUserCommand(image_s3_path=object_key)

    try:
        updated_user = await use_case.execute(user_id=current_user.id, command=command, requester=current_user)
        await session.commit()
        return updated_user
    except Exception as e:
        await session.rollback()
        raise e
