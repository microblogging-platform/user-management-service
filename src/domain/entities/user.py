import datetime
from dataclasses import dataclass, field
from uuid import UUID, uuid4
from ..enums import Role
from ..value_objects import Email, PhoneNumber


@dataclass
class User:
    name: str
    surname: str
    username: str
    password_hash: str
    phone_number: PhoneNumber
    email: Email
    role: Role
    image_s3_path: str
    is_blocked: bool
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=datetime.now)
    modified_at: datetime = field(default_factory=datetime.now)



