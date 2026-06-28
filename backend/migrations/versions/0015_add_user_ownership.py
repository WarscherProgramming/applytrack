"""add user ownership to domain records

Revision ID: 0015
Revises: 0014
Create Date: 2026-06-28

"""

from typing import Sequence, Union
from uuid import uuid4

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0015"
down_revision: Union[str, None] = "0014"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


OWNED_TABLES = (
    "companies",
    "job_applications",
    "recruiters",
    "interviews",
    "followups",
    "resumes",
    "cover_letters",
    "gmail_accounts",
    "email_messages",
    "resume_match_analyses",
    "interview_prep_packages",
    "notifications",
    "calendar_connections",
    "calendar_sync_events",
    "tasks",
)


def upgrade() -> None:
    bind = op.get_bind()
    legacy_user_id = _legacy_owner_id(bind)

    for table in OWNED_TABLES:
        op.add_column(
            table,
            sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        )
        op.create_index(f"ix_{table}_user_id", table, ["user_id"])
        if legacy_user_id is not None:
            bind.execute(
                sa.text(f"UPDATE {table} SET user_id = :user_id WHERE user_id IS NULL"),
                {"user_id": legacy_user_id},
            )
        op.alter_column(table, "user_id", nullable=False)
        op.create_foreign_key(
            f"fk_{table}_user_id",
            table,
            "users",
            ["user_id"],
            ["id"],
            ondelete="CASCADE",
        )

    op.add_column(
        "ai_usage_records",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index("ix_ai_usage_records_user_id", "ai_usage_records", ["user_id"])
    op.create_foreign_key(
        "fk_ai_usage_records_user_id",
        "ai_usage_records",
        "users",
        ["user_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.drop_constraint("uq_companies_name", "companies", type_="unique")
    op.create_unique_constraint("uq_companies_user_name", "companies", ["user_id", "name"])

    op.drop_index("uix_recruiters_email", table_name="recruiters")
    op.create_index(
        "uix_recruiters_user_email",
        "recruiters",
        ["user_id", "email"],
        unique=True,
        postgresql_where=sa.text("email IS NOT NULL"),
    )

    op.drop_constraint("uq_gmail_accounts_email", "gmail_accounts", type_="unique")
    op.create_unique_constraint(
        "uq_gmail_accounts_user_email",
        "gmail_accounts",
        ["user_id", "email_address"],
    )

    op.drop_constraint("notifications_dedupe_key_key", "notifications", type_="unique")
    op.create_unique_constraint(
        "uq_notifications_user_dedupe",
        "notifications",
        ["user_id", "dedupe_key"],
    )

    op.drop_constraint(
        "uq_calendar_connections_provider",
        "calendar_connections",
        type_="unique",
    )
    op.create_unique_constraint(
        "uq_calendar_connections_user_provider",
        "calendar_connections",
        ["user_id", "provider"],
    )

    op.drop_constraint(
        "uq_calendar_sync_provider_item",
        "calendar_sync_events",
        type_="unique",
    )
    op.create_unique_constraint(
        "uq_calendar_sync_user_provider_item",
        "calendar_sync_events",
        ["user_id", "provider", "item_type", "item_id"],
    )

    op.drop_constraint("tasks_source_key_key", "tasks", type_="unique")
    op.create_unique_constraint(
        "uq_tasks_user_source_key",
        "tasks",
        ["user_id", "source_key"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_tasks_user_source_key", "tasks", type_="unique")
    op.create_unique_constraint("tasks_source_key_key", "tasks", ["source_key"])

    op.drop_constraint(
        "uq_calendar_sync_user_provider_item",
        "calendar_sync_events",
        type_="unique",
    )
    op.create_unique_constraint(
        "uq_calendar_sync_provider_item",
        "calendar_sync_events",
        ["provider", "item_type", "item_id"],
    )

    op.drop_constraint(
        "uq_calendar_connections_user_provider",
        "calendar_connections",
        type_="unique",
    )
    op.create_unique_constraint(
        "uq_calendar_connections_provider",
        "calendar_connections",
        ["provider"],
    )

    op.drop_constraint("uq_notifications_user_dedupe", "notifications", type_="unique")
    op.create_unique_constraint(
        "notifications_dedupe_key_key",
        "notifications",
        ["dedupe_key"],
    )

    op.drop_constraint(
        "uq_gmail_accounts_user_email",
        "gmail_accounts",
        type_="unique",
    )
    op.create_unique_constraint(
        "uq_gmail_accounts_email",
        "gmail_accounts",
        ["email_address"],
    )

    op.drop_index("uix_recruiters_user_email", table_name="recruiters")
    op.create_index(
        "uix_recruiters_email",
        "recruiters",
        ["email"],
        unique=True,
        postgresql_where=sa.text("email IS NOT NULL"),
    )

    op.drop_constraint("uq_companies_user_name", "companies", type_="unique")
    op.create_unique_constraint("uq_companies_name", "companies", ["name"])

    op.drop_constraint("fk_ai_usage_records_user_id", "ai_usage_records", type_="foreignkey")
    op.drop_index("ix_ai_usage_records_user_id", table_name="ai_usage_records")
    op.drop_column("ai_usage_records", "user_id")

    for table in reversed(OWNED_TABLES):
        op.drop_constraint(f"fk_{table}_user_id", table, type_="foreignkey")
        op.drop_index(f"ix_{table}_user_id", table_name=table)
        op.drop_column(table, "user_id")


def _legacy_owner_id(bind) -> str | None:
    has_owned_rows = any(
        bind.scalar(sa.text(f"SELECT EXISTS (SELECT 1 FROM {table} LIMIT 1)"))
        for table in OWNED_TABLES
    )
    if not has_owned_rows:
        return None

    existing = bind.scalar(sa.text("SELECT id FROM users ORDER BY created_at ASC LIMIT 1"))
    if existing is not None:
        return str(existing)

    legacy_id = str(uuid4())
    bind.execute(
        sa.text(
            """
            INSERT INTO users
                (id, email, hashed_password, full_name, is_active, created_at, updated_at)
            VALUES
                (
                    :id,
                    'legacy-owner@applytrack.local',
                    'migrated-disabled-password',
                    'Legacy imported data owner',
                    false,
                    now(),
                    now()
                )
            """
        ),
        {"id": legacy_id},
    )
    return legacy_id
