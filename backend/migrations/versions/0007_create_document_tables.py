"""create resumes and cover_letters tables and link them to applications

Revision ID: 0007
Revises: 0006
Create Date: 2026-06-26

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0007"
down_revision: Union[str, None] = "0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _document_table(name: str) -> None:
    """Create one document table (resumes / cover_letters) — identical shape."""
    op.create_table(
        name,
        sa.Column(
            "id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("file_name", sa.String(255), nullable=False),
        sa.Column("storage_path", sa.String(1024), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
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
    )
    op.create_index(f"ix_{name}_name", name, ["name"])


def upgrade() -> None:
    _document_table("resumes")
    _document_table("cover_letters")

    # Link applications to the submitted resume / cover-letter versions.
    # SET NULL on delete: removing a document never deletes the application.
    op.add_column(
        "job_applications",
        sa.Column("resume_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "job_applications",
        sa.Column("cover_letter_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_job_applications_resume_id",
        "job_applications",
        "resumes",
        ["resume_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_job_applications_cover_letter_id",
        "job_applications",
        "cover_letters",
        ["cover_letter_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_job_applications_resume_id", "job_applications", ["resume_id"]
    )
    op.create_index(
        "ix_job_applications_cover_letter_id",
        "job_applications",
        ["cover_letter_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_job_applications_cover_letter_id", table_name="job_applications")
    op.drop_index("ix_job_applications_resume_id", table_name="job_applications")
    op.drop_constraint(
        "fk_job_applications_cover_letter_id", "job_applications", type_="foreignkey"
    )
    op.drop_constraint(
        "fk_job_applications_resume_id", "job_applications", type_="foreignkey"
    )
    op.drop_column("job_applications", "cover_letter_id")
    op.drop_column("job_applications", "resume_id")

    op.drop_index("ix_cover_letters_name", table_name="cover_letters")
    op.drop_table("cover_letters")
    op.drop_index("ix_resumes_name", table_name="resumes")
    op.drop_table("resumes")
