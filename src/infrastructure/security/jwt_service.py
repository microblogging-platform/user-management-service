from datetime import datetime, timedelta, timezone
from typing import Any, Dict
from uuid import UUID

import jwt

from domain.exceptions import ExpiredTokenError, InvalidTokenError
from domain.interfaces.security import ITokenService
from infrastructure.config import settings


class PyJWTService(ITokenService):
    def __init__(self):
        self.secret_key = settings.jwt_secret_key
        self.algorithm = settings.jwt_algorithm
        self.access_token_expire_minutes = settings.access_token_expire_minutes
        self.refresh_token_expire_minutes = settings.refresh_token_expire_minutes
        self.password_reset_token_expire_minutes = settings.password_reset_token_expire_minutes

    def create_access_token(self, data: Dict[str, Any], expires_delta: int | None = None) -> str:
        return self._create_token(
            data=data,
            token_type="access",
            expires_delta=expires_delta or self.access_token_expire_minutes,
        )

    def create_refresh_token(self, data: Dict[str, Any], expires_delta: int | None = None) -> str:
        return self._create_token(
            data=data,
            token_type="refresh",
            expires_delta=expires_delta or self.refresh_token_expire_minutes,
        )

    def create_reset_token(self, data: Dict[str, Any], expires_delta: int | None = None) -> str:
        return self._create_token(
            data=data,
            token_type="reset_password",
            expires_delta=expires_delta or self.password_reset_token_expire_minutes,
        )

    def _create_token(self, data: Dict[str, Any], token_type: str, expires_delta: int) -> str:
        to_encode = data.copy()

        expire = datetime.now(timezone.utc) + timedelta(minutes=expires_delta)

        to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc), "type": token_type})

        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def decode_token(self, token: str) -> Dict[str, Any]:
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload

        except jwt.ExpiredSignatureError as e:
            raise ExpiredTokenError("Token has expired") from e
        except jwt.PyJWTError as e:
            raise InvalidTokenError(f"Could not validate credentials: {str(e)}") from e

    def get_user_id_from_token(self, token: str, expected_type: str = "access") -> UUID:
        payload = self.decode_token(token)

        if payload.get("type") != expected_type:
            raise InvalidTokenError(f"Token type must be '{expected_type}'")

        return payload.get("sub")
