"""create job_applications table

Revision ID: 0002
Revises: 0001
Create Date: 2026-06-24

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "job_applications",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "company_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column("job_title", sa.String(255), nullable=False),
        sa.Column("job_link", sa.String(2000), nullable=True),
        sa.Column("location", sa.String(255), nullable=True),
        sa.Column("salary_range", sa.String(255), nullable=True),
        sa.Column(
            "status",
            sa.String(50),
            nullable=False,
            server_default="draft",
        ),
        sa.Column("date_applied", sa.Date(), nullable=True),
        sa.Column("source", sa.String(255), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
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
            ["company_id"],
            ["companies.id"],
            name="fk_job_applications_company_id",
            # RESTRICT prevents deleting a company that still has applications,
            # avoiding silent data loss. Reassign or delete applications first.
            ondelete="RESTRICT",
        ),
    )
    op.create_index(
        "ix_job_applications_company_id", "job_applications", ["company_id"]
    )
    op.create_index(
        "ix_job_applications_status", "job_applications", ["status"]
    )
    op.create_index(
        "ix_job_applications_date_applied", "job_applications", ["date_applied"]
    )
    op.create_index(
        "ix_job_applications_job_title", "job_applications", ["job_title"]
    )


def downgrade() -> None:
    op.drop_index("ix_job_applications_job_title", table_name="job_applications")
    op.drop_index("ix_job_applications_date_applied", table_name="job_applications")
    op.drop_index("ix_job_applications_status", table_name="job_applications")
    op.drop_index("ix_job_applications_company_id", table_name="job_applications")
    op.drop_table("job_applications")
