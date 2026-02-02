from abc import abstractmethod, ABC
from typing import Any


class ITokenService(ABC):

    @abstractmethod
    def create_access_token(self, data: dict, expires_delta: int | None = None) -> str:
        pass

    @abstractmethod
    def create_refresh_token(self, data: dict, expires_delta: int | None = None) -> str:
        pass

    @abstractmethod
    def decode_token(self, token: str) -> dict[str, Any]:
        pass