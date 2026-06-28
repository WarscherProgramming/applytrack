"""create tasks table

Revision ID: 0013
Revises: 0012
Create Date: 2026-06-27

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0013"
down_revision: Union[str, None] = "0012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tasks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="backlog"),
        sa.Column("priority", sa.String(50), nullable=False, server_default="medium"),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source", sa.String(50), nullable=False, server_default="manual"),
        sa.Column("application_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("recruiter_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("interview_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("followup_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("opportunity_id", sa.String(255), nullable=True),
        sa.Column("source_key", sa.String(255), nullable=True, unique=True),
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
            ["application_id"], ["job_applications.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(
            ["recruiter_id"], ["recruiters.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(["interview_id"], ["interviews.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["followup_id"], ["followups.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_tasks_title", "tasks", ["title"])
    op.create_index("ix_tasks_status", "tasks", ["status"])
    op.create_index("ix_tasks_priority", "tasks", ["priority"])
    op.create_index("ix_tasks_due_date", "tasks", ["due_date"])
    op.create_index("ix_tasks_source", "tasks", ["source"])
    op.create_index("ix_tasks_application_id", "tasks", ["application_id"])
    op.create_index("ix_tasks_company_id", "tasks", ["company_id"])
    op.create_index("ix_tasks_recruiter_id", "tasks", ["recruiter_id"])
    op.create_index("ix_tasks_interview_id", "tasks", ["interview_id"])
    op.create_index("ix_tasks_followup_id", "tasks", ["followup_id"])
    op.create_index("ix_tasks_opportunity_id", "tasks", ["opportunity_id"])
    op.create_index("ix_tasks_source_key", "tasks", ["source_key"])


def downgrade() -> None:
    op.drop_index("ix_tasks_source_key", table_name="tasks")
    op.drop_index("ix_tasks_opportunity_id", table_name="tasks")
    op.drop_index("ix_tasks_followup_id", table_name="tasks")
    op.drop_index("ix_tasks_interview_id", table_name="tasks")
    op.drop_index("ix_tasks_recruiter_id", table_name="tasks")
    op.drop_index("ix_tasks_company_id", table_name="tasks")
    op.drop_index("ix_tasks_application_id", table_name="tasks")
    op.drop_index("ix_tasks_source", table_name="tasks")
    op.drop_index("ix_tasks_due_date", table_name="tasks")
    op.drop_index("ix_tasks_priority", table_name="tasks")
    op.drop_index("ix_tasks_status", table_name="tasks")
    op.drop_index("ix_tasks_title", table_name="tasks")
    op.drop_table("tasks")
