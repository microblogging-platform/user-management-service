from uuid import UUID

from application.usecases.base import UseCase
from domain.exceptions import UserDoesNotExistsError
from domain.interfaces.repositories import IUserRepository
from domain.interfaces.services.storage import IStorageService


class GetUserAvatarInfoUseCase(UseCase):
    def __init__(self, user_repo: IUserRepository, storage_service: IStorageService):
        self._user_repo = user_repo
        self._storage_service = storage_service

    async def execute(self, user_id: UUID) -> dict:
        user = await self._user_repo.get_by_id(user_id)

        if not user:
            raise UserDoesNotExistsError(f"User with id {user_id} not found")

        avatar_url: str | None = None
        if user.image_s3_path:
            avatar_url = await self._storage_service.generate_presigned_get_url(user.image_s3_path)

        return {"username": user.username, "avatar_url": avatar_url}
