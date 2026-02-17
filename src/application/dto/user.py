from typing import Literal
from uuid import UUID

from domain.enums import Role
from pydantic import AwareDatetime, BaseModel, ConfigDict, EmailStr, Field
from pydantic_extra_types.phone_numbers import PhoneNumber


class UpdateUserCommand(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    surname: str | None = Field(default=None, min_length=1, max_length=100)
    username: str | None = Field(default=None, min_length=3, max_length=50)
    phone_number: PhoneNumber | None = None
    email: EmailStr | None = None
    image_s3_path: str | None = None


class UserDTO(BaseModel):
    id: UUID
    name: str
    surname: str
    username: str
    email: EmailStr
    phone_number: PhoneNumber
    image_s3_path: str
    role: Role
    created_at: AwareDatetime

    model_config = ConfigDict(from_attributes=True)


class GetUsersQuery(BaseModel):
    page: int = 1
    limit: int = 30
    filter_by_name: str | None = None
    sort_by: str | None = None
    order_by: Literal["asc", "desc"] = "asc"


class UsersListResponse(BaseModel):
    items: list[UserDTO]
    total: int
    page: int
    limit: int
    pages: int
