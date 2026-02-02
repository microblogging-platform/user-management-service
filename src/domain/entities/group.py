from uuid import UUID, uuid4
from pydantic import Field
from domain.mixins import TimestampMixin

class Group(TimestampMixin):
    id: UUID = Field(default_factory=uuid4)
    name: str = Field(min_length=1)