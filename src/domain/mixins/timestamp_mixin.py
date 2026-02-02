import datetime
from pydantic import AwareDatetime, Field, BaseModel

class TimestampMixin(BaseModel):
    created_at: AwareDatetime = Field(default_factory=lambda: datetime.now(datetime.timezone.utc))
    modified_at: AwareDatetime = Field(default_factory=lambda: datetime.now(datetime.timezone.utc))