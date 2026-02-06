from uuid import UUID, uuid4

from application.usecases.base import UseCase
from domain.interfaces.services.storage import IStorageService
from presentation.api.v1.schemas.user import AvatarPresignedUrlResponse


class InitiateAvatarUploadUseCase(UseCase):
    def __init__(self, storage_service: IStorageService):
        self.storage_service = storage_service

    async def execute(
            self,
            user_id: UUID,
            filename: str,
            content_type: str
    ) -> AvatarPresignedUrlResponse:
        extension = filename.split(".")[-1] if "." in filename else "jpg"
        object_key = f"avatars/{user_id}/{uuid4()}.{extension}"

        upload_url = await self.storage_service.generate_presigned_upload_url(
            object_key=object_key,
            content_type=content_type
        )

        return AvatarPresignedUrlResponse(
            upload_url=upload_url,
            object_key=object_key
        )