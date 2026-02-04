from uuid import UUID

from application.dto.user import UserDTO
from application.usecases.base import UseCase
from domain.entities import User
from domain.exceptions import UserDoesNotExistsError, UserBlockedError
from domain.interfaces.repositories import IUserRepository

class GetCurrentUserUseCase(UseCase):
    def __init__(self, user_repo: IUserRepository):
        self.user_repo = user_repo


    async def execute(self, user_id: UUID) -> UserDTO:
        user: User = await self.user_repo.get_by_id(user_id)

        if not user:
            raise UserDoesNotExistsError("User not found")

        if user.is_blocked:
            raise UserBlockedError("User is blocked")

        return UserDTO.model_validate(user)

