from uuid import UUID, uuid4

from domain.mixins import TimestampMixin
from pydantic import Field


class Group(TimestampMixin):
    id: UUID = Field(default_factory=uuid4)
    name: str = Field(min_length=1)
