"""create interview_prep_packages table

Revision ID: 0010
Revises: 0009
Create Date: 2026-06-27

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0010"
down_revision: Union[str, None] = "0009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "interview_prep_packages",
        sa.Column(
            "id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False
        ),
        sa.Column("application_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("resume_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("company_name", sa.String(255), nullable=False),
        sa.Column("job_title", sa.String(255), nullable=False),
        sa.Column("interview_type", sa.String(100), nullable=True),
        sa.Column("interview_round", sa.String(100), nullable=True),
        sa.Column("job_description", sa.Text(), nullable=False),
        sa.Column("result", postgresql.JSONB(), nullable=False),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("model", sa.String(100), nullable=False),
        sa.Column("prompt_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "completion_tokens", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column("total_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("estimated_cost_usd", sa.Numeric(12, 6), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=False, server_default="0"),
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
        # SET NULL keeps history when an application/resume is deleted.
        sa.ForeignKeyConstraint(
            ["application_id"],
            ["job_applications.id"],
            name="fk_interview_prep_packages_application_id",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["resume_id"],
            ["resumes.id"],
            name="fk_interview_prep_packages_resume_id",
            ondelete="SET NULL",
        ),
    )
    op.create_index(
        "ix_interview_prep_packages_application_id",
        "interview_prep_packages",
        ["application_id"],
    )
    op.create_index(
        "ix_interview_prep_packages_resume_id",
        "interview_prep_packages",
        ["resume_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_interview_prep_packages_resume_id",
        table_name="interview_prep_packages",
    )
    op.drop_index(
        "ix_interview_prep_packages_application_id",
        table_name="interview_prep_packages",
    )
    op.drop_table("interview_prep_packages")
