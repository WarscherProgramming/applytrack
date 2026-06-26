"""create gmail_accounts and email_messages tables

Revision ID: 0006
Revises: 0005
Create Date: 2026-06-26

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "gmail_accounts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("email_address", sa.String(320), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="connected"),
        sa.Column("refresh_token_encrypted", sa.Text(), nullable=True),
        sa.Column("access_token_encrypted", sa.Text(), nullable=True),
        sa.Column("token_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_sync_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_sync_status", sa.String(50), nullable=True),
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
        sa.UniqueConstraint("email_address", name="uq_gmail_accounts_email"),
    )
    op.create_index(
        "ix_gmail_accounts_email_address", "gmail_accounts", ["email_address"]
    )

    op.create_table(
        "email_messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("message_id", sa.String(255), nullable=False),
        sa.Column("thread_id", sa.String(255), nullable=False),
        sa.Column("subject", sa.Text(), nullable=True),
        sa.Column("sender", sa.String(320), nullable=False),
        sa.Column("sender_name", sa.String(255), nullable=True),
        sa.Column("recipients", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("body_preview", sa.Text(), nullable=True),
        sa.Column("direction", sa.String(10), nullable=False),
        sa.Column("labels", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("attachments", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("application_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("recruiter_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("interview_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("match_confidence", sa.Float(), nullable=False, server_default="0"),
        sa.Column("match_reason", sa.String(255), nullable=True),
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
        sa.ForeignKeyConstraint(
            ["account_id"],
            ["gmail_accounts.id"],
            name="fk_email_messages_account_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["company_id"], ["companies.id"],
            name="fk_email_messages_company_id", ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["application_id"], ["job_applications.id"],
            name="fk_email_messages_application_id", ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["recruiter_id"], ["recruiters.id"],
            name="fk_email_messages_recruiter_id", ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["interview_id"], ["interviews.id"],
            name="fk_email_messages_interview_id", ondelete="SET NULL",
        ),
        sa.UniqueConstraint(
            "account_id", "message_id", name="uq_email_messages_account_message"
        ),
    )
    for col in (
        "account_id",
        "message_id",
        "thread_id",
        "sender",
        "sent_at",
        "company_id",
        "application_id",
        "recruiter_id",
        "interview_id",
    ):
        op.create_index(f"ix_email_messages_{col}", "email_messages", [col])


def downgrade() -> None:
    op.drop_table("email_messages")
    op.drop_index("ix_gmail_accounts_email_address", table_name="gmail_accounts")
    op.drop_table("gmail_accounts")
