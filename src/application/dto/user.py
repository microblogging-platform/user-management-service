from uuid import UUID

from domain.enums import Role
from pydantic import AwareDatetime, BaseModel, ConfigDict, EmailStr
from pydantic_extra_types.phone_numbers import PhoneNumber


class RegisterUserCommand(BaseModel):
    name: str
    surname: str
    username: str
    password: str
    email: EmailStr
    phone_number: PhoneNumber

    model_config = ConfigDict(extra="forbid")


class UserDTO(BaseModel):
    id: UUID
    name: str
    surname: str
    username: str
    email: EmailStr
    phone_number: PhoneNumber
    role: Role
    created_at: AwareDatetime

    model_config = ConfigDict(from_attributes=True)


class LoginCommand(BaseModel):
    login: str
    password: str

    model_config = ConfigDict(extra="forbid")


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

    model_config = ConfigDict(from_attributes=True)
