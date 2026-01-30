import datetime
from dataclasses import dataclass
from uuid import UUID
from ..enums import Role
from ..value_objects import Email, PhoneNumber


@dataclass
class User:
    id: UUID
    name: str
    surname: str
    username: str
    password_hash: str
    phone_number: PhoneNumber
    email: Email
    role: Role
    image_s3_path: str
    is_blocked: bool
    created_at: datetime
    modified_at: datetime


