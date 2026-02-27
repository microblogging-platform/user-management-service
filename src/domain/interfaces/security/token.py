from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID


class ITokenService(ABC):
    @abstractmethod
    def create_access_token(self, data: dict, expires_delta: int | None = None) -> str:
        pass

    @abstractmethod
    def create_refresh_token(self, data: dict, expires_delta: int | None = None) -> str:
        pass

    @abstractmethod
    def create_reset_token(self, data: dict, expires_delta: int | None = 15) -> str:
        pass

    @abstractmethod
    def decode_token(self, token: str) -> dict[str, Any]:
        pass

    @abstractmethod
    def get_user_id_from_token(self, token: str) -> UUID:
        pass
