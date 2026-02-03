from domain.interfaces.security import IPasswordHasher
from passlib.context import CryptContext


class Argon2Hasher(IPasswordHasher):
    def __init__(self):
        self._context = CryptContext(
            schemes=["argon2"],
            deprecated="auto",
        )

    def hash(self, password: str) -> str:
        if not password:
            raise ValueError("Password cannot be empty")
        return self._context.hash(password)

    def verify(self, plain_password: str, hashed_password: str) -> bool:
        if not plain_password or not hashed_password:
            return False
        return self._context.verify(plain_password, hashed_password)
