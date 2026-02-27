import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from application.dto.auth import LoginCommand, RegisterUserCommand
from application.usecases.base import UseCase
from domain.exceptions import (
    DomainError,
    InvalidCredentialsError,
    InvalidTokenError,
    UserAlreadyExistsError,
)
from infrastructure.db import get_db_session
from presentation.api.v1.dependencies import (
    get_login_use_case,
    get_refresh_token_use_case,
    get_register_user_use_case,
    get_request_password_reset_use_case,
    get_reset_password_use_case,
)
from presentation.api.v1.schemas.auth import (
    PasswordResetRequest,
    RefreshTokenRequest,
    ResetPasswordConfirmRequest,
    SignupRequest,
    TokenResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", status_code=status.HTTP_201_CREATED)
async def signup(
    request: SignupRequest,
    use_case: Annotated[UseCase, Depends(get_register_user_use_case)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
):
    command = RegisterUserCommand(**request.model_dump())

    try:
        await use_case.execute(command)
        await session.commit()

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
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create user") from e


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
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=e.message, headers={"WWW-Authenticate": "Bearer"}
        ) from e
    except DomainError as e:
        logging.error(f"Error while logging in: {e}", exc_info=True)
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=e.message, headers={"WWW-Authenticate": "Bearer"}
        ) from e
    except Exception as e:
        logging.error(f"Error while logging in: {e}", exc_info=True, headers={"WWW-Authenticate": "Bearer"})
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error while logging in") from e


@router.post("/refresh-token", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def refresh_token(
    request: RefreshTokenRequest,
    use_case: Annotated[UseCase, Depends(get_refresh_token_use_case)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
):
    try:
        tokens = await use_case.execute(request.refresh_token)

        await session.commit()

        return tokens

    except (InvalidCredentialsError, InvalidTokenError) as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e)) from e

    except DomainError as e:
        logging.error(f"Error while refreshing tokens: {e}", exc_info=True)
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message) from e

    except Exception as e:
        logging.error(f"Error while refreshing tokens: {e}", exc_info=True)
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error while refreshing tokens"
        ) from e


@router.post("/request-password-reset", status_code=status.HTTP_200_OK)
async def request_password_reset(
    schema: PasswordResetRequest,
    use_case: Annotated[UseCase, Depends(get_request_password_reset_use_case)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
):
    try:
        await use_case.execute(schema.login)

        return {"detail": "If the user exists, a reset link has been sent."}

    except Exception as e:
        logging.error(f"Error requesting password reset: {e}", exc_info=True)
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An error occurred while processing your request."
        ) from e


@router.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(
    request: ResetPasswordConfirmRequest,
    use_case: Annotated[UseCase, Depends(get_reset_password_use_case)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
):
    try:
        await use_case.execute(request.token, request.new_password)
        await session.commit()
        return {"detail": "Password has been successfully reset"}

    except (InvalidTokenError, InvalidCredentialsError) as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception as e:
        logging.error(f"Error resetting password: {e}", exc_info=True)
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to reset password") from e
