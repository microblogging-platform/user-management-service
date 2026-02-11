from application.dto.auth import LoginCommand, TokenResponse
from application.usecases.base import UseCase
from domain.exceptions import InvalidCredentialsError, UserBlockedError
from domain.interfaces.repositories import IUserRepository
from domain.interfaces.security import IPasswordHasher, ITokenService


class LoginUserUseCase(UseCase):
    def __init__(
        self,
        user_repo: IUserRepository,
        password_hasher: IPasswordHasher,
        token_service: ITokenService,
    ):
        self.user_repo = user_repo
        self.password_hasher = password_hasher
        self.token_service = token_service

    async def execute(self, command: LoginCommand) -> TokenResponse:
        user = await self.user_repo.get_by_login_identifier(command.login)

        if not user:
            raise InvalidCredentialsError("Invalid username, email or phone number")

        if not await self.password_hasher.verify(command.password, user.password_hash):
            raise InvalidCredentialsError("Incorrect password")

        if user.is_blocked:
            raise UserBlockedError("Your account has been blocked.")

        access_token = self.token_service.create_access_token(data={"sub": str(user.id), "role": user.role.value})

        refresh_token = self.token_service.create_refresh_token(data={"sub": str(user.id)})

        return TokenResponse(access_token=access_token, refresh_token=refresh_token)
