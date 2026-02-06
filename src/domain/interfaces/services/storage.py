from abc import ABC, abstractmethod
from typing import BinaryIO


class IStorageService(ABC):
    @abstractmethod
    async def upload_file(self, file: BinaryIO, filename: str, content_type: str) -> str:
        pass

    @abstractmethod
    async def delete_file(self, file_path: str):
        pass