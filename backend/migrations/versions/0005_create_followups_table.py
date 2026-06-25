"""create followups table

Revision ID: 0005
Revises: 0004
Create Date: 2026-06-24

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "followups",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "application_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "recruiter_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column(
            "interview_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("followup_type", sa.String(50), nullable=False),
        sa.Column(
            "status",
            sa.String(50),
            nullable=False,
            server_default="pending",
        ),
        sa.Column(
            "priority",
            sa.String(50),
            nullable=False,
            server_default="medium",
        ),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
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
        # CASCADE: follow-ups are structurally owned by their application.
        sa.ForeignKeyConstraint(
            ["application_id"],
            ["job_applications.id"],
            name="fk_followups_application_id",
            ondelete="CASCADE",
        ),
        # SET NULL: deleting a recruiter/interview must not destroy the reminder.
        sa.ForeignKeyConstraint(
            ["recruiter_id"],
            ["recruiters.id"],
            name="fk_followups_recruiter_id",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["interview_id"],
            ["interviews.id"],
            name="fk_followups_interview_id",
            ondelete="SET NULL",
        ),
    )

    op.create_index("ix_followups_application_id", "followups", ["application_id"])
    op.create_index("ix_followups_recruiter_id", "followups", ["recruiter_id"])
    op.create_index("ix_followups_interview_id", "followups", ["interview_id"])
    op.create_index("ix_followups_followup_type", "followups", ["followup_type"])
    op.create_index("ix_followups_status", "followups", ["status"])
    op.create_index("ix_followups_priority", "followups", ["priority"])
    op.create_index("ix_followups_due_date", "followups", ["due_date"])


def downgrade() -> None:
    op.drop_index("ix_followups_due_date", table_name="followups")
    op.drop_index("ix_followups_priority", table_name="followups")
    op.drop_index("ix_followups_status", table_name="followups")
    op.drop_index("ix_followups_followup_type", table_name="followups")
    op.drop_index("ix_followups_interview_id", table_name="followups")
    op.drop_index("ix_followups_recruiter_id", table_name="followups")
    op.drop_index("ix_followups_application_id", table_name="followups")
    op.drop_table("followups")
