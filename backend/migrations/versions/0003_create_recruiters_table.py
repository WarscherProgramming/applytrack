"""create recruiters table

Revision ID: 0003
Revises: 0002
Create Date: 2026-06-24

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "recruiters",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "company_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column("first_name", sa.String(255), nullable=True),
        sa.Column("last_name", sa.String(255), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("title", sa.String(255), nullable=True),
        sa.Column("linkedin_url", sa.String(2000), nullable=True),
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
            name="fk_recruiters_company_id",
            # SET NULL keeps the contact record alive when the linked company
            # is deleted. RESTRICT would block company deletion; CASCADE
            # would silently destroy contacts.
            ondelete="SET NULL",
        ),
    )

    op.create_index("ix_recruiters_company_id", "recruiters", ["company_id"])
    op.create_index("ix_recruiters_title", "recruiters", ["title"])

    # Partial unique index: enforce email uniqueness only for non-null values.
    # A plain UNIQUE constraint would work the same way in PostgreSQL (NULLs are
    # distinct), but the explicit partial index makes the intent unambiguous and
    # avoids relying on database-specific NULL handling of unique constraints.
    op.create_index(
        "uix_recruiters_email",
        "recruiters",
        ["email"],
        unique=True,
        postgresql_where=sa.text("email IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("uix_recruiters_email", table_name="recruiters")
    op.drop_index("ix_recruiters_title", table_name="recruiters")
    op.drop_index("ix_recruiters_company_id", table_name="recruiters")
    op.drop_table("recruiters")
