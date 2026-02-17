import asyncio

from argon2 import PasswordHasher as Argon2PasswordHasher
from argon2.exceptions import VerifyMismatchError

from domain.interfaces.security import IPasswordHasher


class Argon2Hasher(IPasswordHasher):
    def __init__(self):
        self._ph = Argon2PasswordHasher()

    async def hash(self, password: str) -> str:
        if not password:
            raise ValueError("Password cannot be empty")

        return await asyncio.to_thread(self._ph.hash, password)

    async def verify(self, password: str, hashed_password: str) -> bool:
        if not password or not hashed_password:
            return False

        def _verify_sync():
            try:
                return self._ph.verify(hashed_password, password)
            except VerifyMismatchError:
                return False

        return await asyncio.to_thread(_verify_sync)
