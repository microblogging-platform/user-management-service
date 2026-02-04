from uuid import UUID
from datetime import datetime, timezone
from application.usecases.base import UseCase
from application.dto.user import UpdateUserCommand, UserDTO
from domain.interfaces.repositories import IUserRepository
from domain.exceptions import DomainError, UserAlreadyExistsError


class UpdateUserUseCase(UseCase):
    def __init__(self, user_repo: IUserRepository):
        self.user_repo = user_repo

    async def execute(self, user_id: UUID, command: UpdateUserCommand) -> UserDTO:
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise DomainError("User not found")

        if command.username and command.username != user.username:
            if await self.user_repo.get_by_login_identifier(command.username):
                raise UserAlreadyExistsError("Username already taken")

        if command.email and command.email != user.email:
            if await self.user_repo.get_by_login_identifier(command.email):
                raise UserAlreadyExistsError("Email already taken")

        if command.phone_number and command.phone_number != user.phone_number:
            if await self.user_repo.get_by_login_identifier(command.phone_number):
                raise UserAlreadyExistsError("Phone number already taken")

        updated_data = command.model_dump(exclude_unset=True)

        for key, value in updated_data.items():
            if hasattr(user, key):
                setattr(user, key, value)

        user.modified_at = datetime.now(timezone.utc)

        updated_user = await self.user_repo.update(user)

        return UserDTO.model_validate(updated_user)