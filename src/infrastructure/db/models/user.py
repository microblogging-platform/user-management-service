from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from domain.enums import Role
from infrastructure.db import Base
from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship


def utc_now():
    datetime.now(timezone.utc)


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4, server_default=None)

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    surname: Mapped[str] = mapped_column(String(100), nullable=False)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    phone_number: Mapped[str] = mapped_column(String(20), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)

    role: Mapped[Role] = mapped_column(
        SQLEnum(Role, native_enum=False, values_callable=lambda x: [e.value for e in Role]),
        nullable=False,
        default=Role.USER,
    )

    image_s3_path: Mapped[str] = mapped_column(String(500), nullable=False)
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    group_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("groups.id"), nullable=True, index=True)

    group: Mapped[Optional["GroupModel"]] = relationship("GroupModel", back_populates="users", lazy="selectin")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    modified_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )

    __table_args__ = (
        Index("idx_users_username", "username"),
        Index("idx_users_email", "email"),
        Index("idx_users_group_id", "group_id"),
        Index("idx_users_role", "role"),
    )
