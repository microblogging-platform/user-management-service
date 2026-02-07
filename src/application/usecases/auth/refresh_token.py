from application.dto.auth import TokenResponse
from application.usecases.base import UseCase
from domain.exceptions import InvalidTokenError, InvalidCredentialsError
from domain.interfaces.repositories import IUserRepository
from domain.interfaces.security import ITokenService


class RefreshTokenUseCase(UseCase):
    def __init__(self, user_repo: IUserRepository, token_service: ITokenService):
        self.user_repo = user_repo
        self.token_service = token_service

    async def execute(self, refresh_token: str) -> TokenResponse:
        try:
            payload = self.token_service.decode_token(refresh_token)
        except Exception:
            raise InvalidTokenError("Invalid refresh token")

        if payload.get("type") != "refresh":
            raise InvalidTokenError("Token is not a refresh token")

        user_id = payload.get("sub")
        user = await self.user_repo.get_by_id(user_id)

        if not user:
            raise InvalidCredentialsError("User no longer exists")

        new_access = self.token_service.create_access_token(data={"sub": str(user.id), "role": user.role.value})
        new_refresh = self.token_service.create_refresh_token(data={"sub": str(user.id)})

        return TokenResponse(access_token=new_access, refresh_token=new_refresh)
