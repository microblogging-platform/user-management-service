from abc import ABC, abstractmethod


class ITokenBlacklistService(ABC):
    @abstractmethod
    async def blacklist_token(self, token: str, expires_at: int) -> None:
        pass

    @abstractmethod
    async def is_blacklisted(self, token: str) -> bool:
        pass
