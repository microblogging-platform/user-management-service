from datetime import datetime, timezone
from typing import TYPE_CHECKING, List
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from infrastructure.db import Base

if TYPE_CHECKING:
    from infrastructure.db.models import UserModel


def utc_now() -> datetime:
    """Return current UTC datetime for default/onupdate."""
    return datetime.now(timezone.utc)


class GroupModel(Base):
    __tablename__ = "groups"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4, server_default=None)

    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    modified_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )

    users: Mapped[List["UserModel"]] = relationship("UserModel", back_populates="group", lazy="selectin")

    __table_args__ = (Index("idx_groups_name", "name"),)
