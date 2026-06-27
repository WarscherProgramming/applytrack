"""create notifications table

Revision ID: 0011
Revises: 0010
Create Date: 2026-06-27

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0011"
down_revision: Union[str, None] = "0010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "notifications",
        sa.Column(
            "id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False
        ),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("priority", sa.String(50), nullable=False),
        sa.Column("source_type", sa.String(100), nullable=True),
        sa.Column("source_id", sa.String(255), nullable=True),
        sa.Column("action_url", sa.String(500), nullable=True),
        sa.Column("dedupe_key", sa.String(255), nullable=False, unique=True),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_pinned", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_dismissed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_notifications_category", "notifications", ["category"])
    op.create_index("ix_notifications_priority", "notifications", ["priority"])
    op.create_index("ix_notifications_source_type", "notifications", ["source_type"])
    op.create_index("ix_notifications_source_id", "notifications", ["source_id"])
    op.create_index("ix_notifications_dedupe_key", "notifications", ["dedupe_key"])
    op.create_index("ix_notifications_is_read", "notifications", ["is_read"])
    op.create_index("ix_notifications_is_pinned", "notifications", ["is_pinned"])
    op.create_index("ix_notifications_is_dismissed", "notifications", ["is_dismissed"])


def downgrade() -> None:
    op.drop_index("ix_notifications_is_dismissed", table_name="notifications")
    op.drop_index("ix_notifications_is_pinned", table_name="notifications")
    op.drop_index("ix_notifications_is_read", table_name="notifications")
    op.drop_index("ix_notifications_dedupe_key", table_name="notifications")
    op.drop_index("ix_notifications_source_id", table_name="notifications")
    op.drop_index("ix_notifications_source_type", table_name="notifications")
    op.drop_index("ix_notifications_priority", table_name="notifications")
    op.drop_index("ix_notifications_category", table_name="notifications")
    op.drop_table("notifications")
