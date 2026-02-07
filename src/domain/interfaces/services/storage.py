from abc import ABC, abstractmethod
from typing import BinaryIO


class IStorageService(ABC):
    @abstractmethod
    async def upload_file(self, file: BinaryIO, filename: str, content_type: str) -> str:
        pass

    @abstractmethod
    async def delete_file(self, file_path: str):
        pass

    @abstractmethod
    async def generate_presigned_upload_url(self, object_key: str, content_type: str, expires_in: int = 3600) -> str:
        pass

    @abstractmethod
    async def generate_presigned_get_url(self, object_key: str, expires_in: int = 3600) -> str | None:
        pass
