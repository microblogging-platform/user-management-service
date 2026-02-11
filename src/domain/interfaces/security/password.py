from abc import ABC, abstractmethod


class IPasswordHasher(ABC):

    @abstractmethod
    async def hash(self, password: str) -> str:
        pass

    @abstractmethod
    async def verify(self, plain_password: str, hashed_password: str) -> bool:
        pass
