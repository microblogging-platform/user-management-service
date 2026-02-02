import jwt
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from domain.interfaces.security import ITokenService
from domain.exceptions import InvalidTokenError, ExpiredTokenError
from infrastructure.config import settings


class PyJWTService(ITokenService):
    def __init__(self):
        self.secret_key = settings.jwt_secret_key
        self.algorithm = settings.jwt_algorithm
        self.access_token_expire_minutes = settings.access_token_expire_minutes
        self.refresh_token_expire_minutes = settings.refresh_token_expire_minutes

    def create_access_token(self, data: Dict[str, Any], expires_delta: int | None = None) -> str:
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.now(timezone.utc) + timedelta(minutes=expires_delta)
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=self.access_token_expire_minutes)

        to_encode.update({
            "exp": expire,
            "iat": datetime.now(timezone.utc)
        })

        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def create_refresh_token(self, data: Dict[str, Any], expires_delta: int | None = None) -> str:
        return self.create_access_token(data, expires_delta=self.refresh_token_expire_minutes)

    def decode_token(self, token: str) -> Dict[str, Any]:
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload

        except jwt.ExpiredSignatureError:
            raise ExpiredTokenError("Token has expired")
        except jwt.PyJWTError as e:
            raise InvalidTokenError(f"Could not validate credentials: {str(e)}")