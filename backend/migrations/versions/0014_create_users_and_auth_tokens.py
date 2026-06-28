"""create users and auth refresh tokens

Revision ID: 0014
Revises: 0013
Create Date: 2026-06-28

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0014"
down_revision: Union[str, None] = "0013"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("email", sa.String(320), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
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
    op.create_index("ix_users_email", "users", ["email"])
    op.create_index("ix_users_is_active", "users", ["is_active"])

    op.create_table(
        "auth_refresh_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_auth_refresh_tokens_user_id", "auth_refresh_tokens", ["user_id"])
    op.create_index(
        "ix_auth_refresh_tokens_token_hash",
        "auth_refresh_tokens",
        ["token_hash"],
    )
    op.create_index(
        "ix_auth_refresh_tokens_revoked_at",
        "auth_refresh_tokens",
        ["revoked_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_auth_refresh_tokens_revoked_at", table_name="auth_refresh_tokens")
    op.drop_index("ix_auth_refresh_tokens_token_hash", table_name="auth_refresh_tokens")
    op.drop_index("ix_auth_refresh_tokens_user_id", table_name="auth_refresh_tokens")
    op.drop_table("auth_refresh_tokens")
    op.drop_index("ix_users_is_active", table_name="users")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
