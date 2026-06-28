"""create calendar integration tables

Revision ID: 0012
Revises: 0011
Create Date: 2026-06-27

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0012"
down_revision: Union[str, None] = "0011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "calendar_connections",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="disconnected"),
        sa.Column("account_email", sa.String(320), nullable=True),
        sa.Column("calendar_id", sa.String(255), nullable=True),
        sa.Column("access_token_encrypted", sa.Text(), nullable=True),
        sa.Column("refresh_token_encrypted", sa.Text(), nullable=True),
        sa.Column("token_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_sync_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_sync_status", sa.String(50), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
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
        sa.UniqueConstraint("provider", name="uq_calendar_connections_provider"),
    )
    op.create_index("ix_calendar_connections_provider", "calendar_connections", ["provider"])

    op.create_table(
        "calendar_sync_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("item_type", sa.String(50), nullable=False),
        sa.Column("item_id", sa.String(255), nullable=False),
        sa.Column("external_event_id", sa.String(255), nullable=False),
        sa.Column("event_hash", sa.String(64), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="synced"),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
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
        sa.UniqueConstraint(
            "provider",
            "item_type",
            "item_id",
            name="uq_calendar_sync_provider_item",
        ),
    )
    op.create_index("ix_calendar_sync_events_provider", "calendar_sync_events", ["provider"])
    op.create_index("ix_calendar_sync_events_item_type", "calendar_sync_events", ["item_type"])
    op.create_index("ix_calendar_sync_events_item_id", "calendar_sync_events", ["item_id"])
    op.create_index(
        "ix_calendar_sync_events_external_event_id",
        "calendar_sync_events",
        ["external_event_id"],
    )
    op.create_index("ix_calendar_sync_events_status", "calendar_sync_events", ["status"])


def downgrade() -> None:
    op.drop_index("ix_calendar_sync_events_status", table_name="calendar_sync_events")
    op.drop_index("ix_calendar_sync_events_external_event_id", table_name="calendar_sync_events")
    op.drop_index("ix_calendar_sync_events_item_id", table_name="calendar_sync_events")
    op.drop_index("ix_calendar_sync_events_item_type", table_name="calendar_sync_events")
    op.drop_index("ix_calendar_sync_events_provider", table_name="calendar_sync_events")
    op.drop_table("calendar_sync_events")
    op.drop_index("ix_calendar_connections_provider", table_name="calendar_connections")
    op.drop_table("calendar_connections")
