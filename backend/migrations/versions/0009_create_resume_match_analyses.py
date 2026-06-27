"""create resume_match_analyses table

Revision ID: 0009
Revises: 0008
Create Date: 2026-06-26

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0009"
down_revision: Union[str, None] = "0008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "resume_match_analyses",
        sa.Column(
            "id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False
        ),
        sa.Column("resume_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("resume_name", sa.String(255), nullable=False),
        sa.Column("job_description", sa.Text(), nullable=False),
        sa.Column("overall_match_score", sa.Integer(), nullable=False),
        sa.Column("result", postgresql.JSONB(), nullable=False),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("model", sa.String(100), nullable=False),
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
        # SET NULL keeps analysis history when a resume is deleted.
        sa.ForeignKeyConstraint(
            ["resume_id"],
            ["resumes.id"],
            name="fk_resume_match_analyses_resume_id",
            ondelete="SET NULL",
        ),
    )
    op.create_index(
        "ix_resume_match_analyses_resume_id", "resume_match_analyses", ["resume_id"]
    )
    op.create_index(
        "ix_resume_match_analyses_overall_match_score",
        "resume_match_analyses",
        ["overall_match_score"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_resume_match_analyses_overall_match_score",
        table_name="resume_match_analyses",
    )
    op.drop_index(
        "ix_resume_match_analyses_resume_id", table_name="resume_match_analyses"
    )
    op.drop_table("resume_match_analyses")
