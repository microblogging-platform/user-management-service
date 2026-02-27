"""add modified_at field to group

Revision ID: 404b4d5da71a
Revises: f367e55e53e7
Create Date: 2026-02-11 16:41:18.574853

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "404b4d5da71a"
down_revision: Union[str, Sequence[str], None] = "f367e55e53e7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "groups",
        sa.Column(
            "modified_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.alter_column("groups", "modified_at", server_default=None)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("groups", "modified_at")
