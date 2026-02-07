from datetime import datetime
from typing import List
from uuid import UUID, uuid4

from infrastructure.db import Base
from sqlalchemy import DateTime, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship


class GroupModel(Base):
    __tablename__ = "groups"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4, server_default=None)

    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    users: Mapped[List["UserModel"]] = relationship("UserModel", back_populates="group", lazy="selectin")

    __table_args__ = (Index("idx_groups_name", "name"),)
