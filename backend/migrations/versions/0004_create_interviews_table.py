"""create interviews table

Revision ID: 0004
Revises: 0003
Create Date: 2026-06-24

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "interviews",
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
        sa.Column("interview_type", sa.String(50), nullable=True),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "duration_minutes",
            sa.Integer(),
            nullable=False,
            server_default="30",
        ),
        sa.Column("location", sa.String(255), nullable=True),
        sa.Column("meeting_link", sa.String(2000), nullable=True),
        sa.Column(
            "status",
            sa.String(50),
            nullable=False,
            server_default="scheduled",
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("feedback", sa.Text(), nullable=True),
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
        # CASCADE: interviews are structurally owned by applications.
        # Deleting an application cascades to its interviews, avoiding the
        # "delete all interviews first" friction that RESTRICT would impose.
        sa.ForeignKeyConstraint(
            ["application_id"],
            ["job_applications.id"],
            name="fk_interviews_application_id",
            ondelete="CASCADE",
        ),
        # SET NULL: a recruiter deletion should not destroy interview records.
        # The interview history is still meaningful without the recruiter link.
        sa.ForeignKeyConstraint(
            ["recruiter_id"],
            ["recruiters.id"],
            name="fk_interviews_recruiter_id",
            ondelete="SET NULL",
        ),
    )

    op.create_index("ix_interviews_application_id", "interviews", ["application_id"])
    op.create_index("ix_interviews_recruiter_id", "interviews", ["recruiter_id"])
    op.create_index("ix_interviews_status", "interviews", ["status"])
    op.create_index("ix_interviews_interview_type", "interviews", ["interview_type"])
    op.create_index("ix_interviews_scheduled_at", "interviews", ["scheduled_at"])


def downgrade() -> None:
    op.drop_index("ix_interviews_scheduled_at", table_name="interviews")
    op.drop_index("ix_interviews_interview_type", table_name="interviews")
    op.drop_index("ix_interviews_status", table_name="interviews")
    op.drop_index("ix_interviews_recruiter_id", table_name="interviews")
    op.drop_index("ix_interviews_application_id", table_name="interviews")
    op.drop_table("interviews")
