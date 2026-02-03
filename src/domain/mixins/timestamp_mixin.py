from datetime import datetime, timezone
from pydantic import AwareDatetime, Field, BaseModel

class TimestampMixin(BaseModel):
    created_at: AwareDatetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    modified_at: AwareDatetime = Field(default_factory=lambda: datetime.now(timezone.utc))