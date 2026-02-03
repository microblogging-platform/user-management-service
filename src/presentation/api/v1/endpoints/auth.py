import logging
from typing import Annotated

from fastapi.security import OAuth2PasswordRequestForm

from application.dto.user import LoginCommand, RegisterUserCommand
from application.usecases.base import UseCase
from domain.exceptions import (
    DomainError,
    InvalidCredentialsError,
    UserAlreadyExistsError,
)
from fastapi import APIRouter, Depends, HTTPException, status
from infrastructure.db import get_db_session
from presentation.api.v1.dependencies import (
    get_login_use_case,
    get_register_user_use_case,
)
from presentation.api.v1.schemas.auth import (
    LoginRequest,
    SignupRequest,
    SignupResponse,
    TokenResponse,
)
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/signup", response_model=SignupResponse, status_code=status.HTTP_201_CREATED
)
async def signup(
    request: SignupRequest,
    use_case: Annotated[UseCase, Depends(get_register_user_use_case)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> SignupResponse:
    command = RegisterUserCommand(**request.model_dump())

    try:
        user_dto = await use_case.execute(command)

        await session.commit()

        return SignupResponse.model_validate(user_dto)

    except UserAlreadyExistsError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=e.message) from e
    except DomainError as e:
        logging.error(f"Error registering user: {e}", exc_info=True)
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message) from e
    except Exception as e:
        logging.error(f"Error registering user: {e}", exc_info=True)
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user",
        ) from e


@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def login(
    request: Annotated[OAuth2PasswordRequestForm, Depends()],
    use_case: Annotated[UseCase, Depends(get_login_use_case)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
):
    command = LoginCommand(login=request.username, password=request.password)

    try:
        tokens = await use_case.execute(command)

        await session.commit()

        return tokens

    except InvalidCredentialsError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=e.message) from e
    except DomainError as e:
        logging.error(f"Error while logging in: {e}", exc_info=True)
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message) from e
    except Exception as e:
        logging.error(f"Error while logging in: {e}", exc_info=True)
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error while logging in",
        ) from e
