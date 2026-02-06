from uuid import UUID

from pydantic import BaseModel, EmailStr, AwareDatetime, ConfigDict
from pydantic_extra_types.phone_numbers import PhoneNumber

from domain.enums import Role


class UpdateUserRequest(BaseModel):
    name: str | None = None
    surname: str | None = None
    username: str | None = None
    phone_number: PhoneNumber | None = None
    email: EmailStr | None = None
    image_s3_path: str | None = None

class UserResponse(BaseModel):
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

class AvatarUploadRequest(BaseModel):
    filename: str
    content_type: str

class AvatarPresignedUrlResponse(BaseModel):
    upload_url: str
    object_key: str