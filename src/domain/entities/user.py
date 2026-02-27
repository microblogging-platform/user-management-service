from uuid import UUID, uuid4

from pydantic import ConfigDict, EmailStr, Field
from pydantic_extra_types.phone_numbers import PhoneNumber

from domain.enums import Role
from domain.mixins import TimestampMixin


class User(TimestampMixin):
    id: UUID = Field(default_factory=uuid4)
    name: str = Field(min_length=1)
    surname: str = Field(min_length=1)
    username: str = Field(min_length=3)
    password_hash: str
    email: EmailStr
    phone_number: PhoneNumber
    role: Role
    image_s3_path: str
    is_blocked: bool
    group_id: UUID | None = None

    model_config = ConfigDict(from_attributes=True)
