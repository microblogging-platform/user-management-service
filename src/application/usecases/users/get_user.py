from uuid import UUID
from application.dto.user import UserDTO
from application.usecases.base import UseCase
from domain.entities.user import User
from domain.enums.roles import Role
from domain.exceptions import UserDoesNotExistsError, ForbiddenError
from domain.interfaces.repositories import IUserRepository


class GetUserByIdUseCase(UseCase):
    def __init__(self, user_repo: IUserRepository):
        self.user_repo = user_repo

    async def execute(self, user_id: UUID, requester: User) -> UserDTO:
        target_user = await self.user_repo.get_by_id(user_id)

        if not target_user:
            raise UserDoesNotExistsError(f"User with id {user_id} not found")

        if requester.role == Role.ADMIN:
            return UserDTO.model_validate(target_user)

        if requester.role == Role.MODERATOR:
            if requester.group_id is not None and target_user.group_id == requester.group_id:
                return UserDTO.model_validate(target_user)

        if requester.id == target_user.id:
            return UserDTO.model_validate(target_user)

        raise ForbiddenError("You don't have permission to access this user profile")