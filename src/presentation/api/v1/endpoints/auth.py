from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.db import get_db_session
from presentation.api.v1.schemas.auth import SignupRequest, SignupResponse
from presentation.api.v1.dependencies import get_register_user_use_case
from application.usecases.auth.register_user import RegisterUserUseCase
from application.dto.user import RegisterUserCommand
from domain.exceptions import UserAlreadyExistsError, DomainError

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=SignupResponse, status_code=status.HTTP_201_CREATED)
async def signup(
        request: SignupRequest,
        use_case: Annotated[RegisterUserUseCase, Depends(get_register_user_use_case)],
        session: Annotated[AsyncSession, Depends(get_db_session)]
) -> SignupResponse:
    command = RegisterUserCommand(**request.model_dump())

    try:
        user_dto = await use_case.execute(command)

        await session.commit()

        # Вместо перечисления всех полей:
        return SignupResponse.model_validate(user_dto)

    except UserAlreadyExistsError as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except DomainError as e:
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