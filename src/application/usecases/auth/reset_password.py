from application.usecases.base import UseCase
from domain.exceptions import InvalidCredentialsError, InvalidTokenError
from domain.interfaces.repositories import IUserRepository
from domain.interfaces.security import IPasswordHasher, ITokenService
from domain.interfaces.services.blacklist import ITokenBlacklistService


class ResetPasswordUseCase(UseCase):
    def __init__(
        self,
        user_repo: IUserRepository,
        token_service: ITokenService,
        password_hasher: IPasswordHasher,
        blacklist_service: ITokenBlacklistService,
    ):
        self.user_repo = user_repo
        self.token_service = token_service
        self.password_hasher = password_hasher
        self.blacklist_service = blacklist_service

    async def execute(self, token: str, new_password: str) -> None:
        if await self.blacklist_service.is_blacklisted(token):
            raise InvalidTokenError("Token has already been used")

        try:
            payload = self.token_service.decode_token(token)
        except Exception as e:
            raise InvalidTokenError("Invalid or expired token") from e

        if payload.get("type") != "reset_password":
            raise InvalidTokenError("Token is not a password reset token")

        user_id = payload.get("sub")
        exp_timestamp = payload.get("exp")

        if not await self.user_repo.exists_by_id(user_id):
            raise InvalidCredentialsError("User not found")

        hashed_password = await self.password_hasher.hash(new_password)

        await self.user_repo.update_password(user_id, hashed_password)

        if exp_timestamp:
            await self.blacklist_service.blacklist_token(token, expires_at=exp_timestamp)
