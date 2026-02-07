from uuid import UUID
from application.dto.user import UserDTO
from application.usecases.base import UseCase
from domain.entities.user import User
from domain.enums.roles import Role
from domain.exceptions import UserDoesNotExistsError, ForbiddenError
from domain.interfaces.repositories import IUserRepository
from domain.interfaces.services.storage import IStorageService


class GetUserByIdUseCase(UseCase):
    def __init__(self, user_repo: IUserRepository, storage_service: IStorageService):
        self._user_repo = user_repo
        self._storage_service = storage_service

    async def execute(self, user_id: UUID, requester: User) -> UserDTO:
        target_user = await self._user_repo.get_by_id(user_id)

        if not target_user:
            raise UserDoesNotExistsError(f"User with id {user_id} not found")

        user_dto = UserDTO.model_validate(target_user)

        if target_user.image_s3_path:
            user_dto.image_s3_path = await self._storage_service.generate_presigned_get_url(target_user.image_s3_path)

        if requester.role == Role.ADMIN:
            return user_dto

        if requester.role == Role.MODERATOR:
            if requester.group_id is not None and target_user.group_id == requester.group_id:
                return user_dto

        if requester.id == target_user.id:
            return user_dto

        raise ForbiddenError("You don't have permission to access this user profile")
