from abc import abstractmethod
from typing import Protocol, Any


class ITokenService(Protocol):

    @abstractmethod
    def create_access_token(self, data: dict, expires_delta: int | None = None) -> str:
        pass

    @abstractmethod
    def decode_token(self, token: str) -> dict[str, Any]:
        pass