import datetime
from dataclasses import dataclass
from enum import Enum
from uuid import UUID
from ..value_objects import Email, PhoneNumber

class Role(Enum):
    USER = "USER"
    ADMIN = "ADMIN"
    MODERATOR = "MODERATOR"


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


