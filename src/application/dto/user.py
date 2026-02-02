from uuid import UUID
from pydantic import BaseModel, EmailStr, ConfigDict
from pydantic_extra_types.phone_numbers import PhoneNumber
from domain.enums import Role


class RegisterUserCommand(BaseModel):
    name: str
    surname: str
    username: str
    password: str
    email: EmailStr
    phone_number: PhoneNumber

    model_config = ConfigDict(extra='forbid')


class UserDTO(BaseModel):
    id: UUID
    name: str
    surname: str
    username: str
    email: EmailStr
    phone_number: PhoneNumber
    role: Role

    model_config = ConfigDict(from_attributes=True)