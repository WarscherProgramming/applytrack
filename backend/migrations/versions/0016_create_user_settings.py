"""create user settings table

Revision ID: 0016
Revises: 0015
Create Date: 2026-06-28

"""

from typing import Sequence, Union
from uuid import uuid4

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0016"
down_revision: Union[str, None] = "0015"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user_settings",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("timezone", sa.String(length=64), nullable=False, server_default="UTC"),
        sa.Column(
            "notification_preferences",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("theme", sa.String(length=20), nullable=False, server_default="system"),
        sa.Column(
            "default_dashboard_page",
            sa.String(length=80),
            nullable=False,
            server_default="career_copilot",
        ),
        sa.Column(
            "default_notification_behavior",
            sa.String(length=40),
            nullable=False,
            server_default="all",
        ),
        sa.Column(
            "preferred_calendar_provider",
            sa.String(length=40),
            nullable=False,
            server_default="ics",
        ),
        sa.Column(
            "preferred_ai_provider",
            sa.String(length=40),
            nullable=False,
            server_default="auto",
        ),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_user_settings_user_id", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", name="uq_user_settings_user_id"),
    )
    op.create_index("ix_user_settings_user_id", "user_settings", ["user_id"])

    bind = op.get_bind()
    for (user_id,) in bind.execute(sa.text("SELECT id FROM users")):
        bind.execute(
            sa.text(
                """
                INSERT INTO user_settings
                    (
                        id,
                        user_id,
                        timezone,
                        notification_preferences,
                        theme,
                        default_dashboard_page,
                        default_notification_behavior,
                        preferred_calendar_provider,
                        preferred_ai_provider,
                        created_at,
                        updated_at
                    )
                VALUES
                    (
                        :id,
                        :user_id,
                        'UTC',
                        '{}'::jsonb,
                        'system',
                        'career_copilot',
                        'all',
                        'ics',
                        'auto',
                        now(),
                        now()
                    )
                ON CONFLICT (user_id) DO NOTHING
                """
            ),
            {"id": str(uuid4()), "user_id": user_id},
        )


def downgrade() -> None:
    op.drop_index("ix_user_settings_user_id", table_name="user_settings")
    op.drop_table("user_settings")
