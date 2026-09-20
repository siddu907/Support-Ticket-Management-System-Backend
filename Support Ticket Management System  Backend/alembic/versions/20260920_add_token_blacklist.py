"""Add token blacklist table for logged-out JWT invalidation.

Revision ID: 20260920_token_blacklist
Revises: 20260919_indexes
Create Date: 2026-09-20

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260920_token_blacklist"
down_revision: Union[str, Sequence[str], None] = "20260919_indexes"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "token_blacklist",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("jti", sa.String(length=255), nullable=False),
        sa.Column("token_type", sa.String(length=20), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_revoked", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_token_blacklist_id"), "token_blacklist", ["id"], unique=False)
    op.create_index(op.f("ix_token_blacklist_user_id"), "token_blacklist", ["user_id"], unique=False)
    op.create_index(op.f("ix_token_blacklist_jti"), "token_blacklist", ["jti"], unique=False)
    op.create_index(op.f("ix_token_blacklist_token_type"), "token_blacklist", ["token_type"], unique=False)
    op.create_index(op.f("ix_token_blacklist_is_revoked"), "token_blacklist", ["is_revoked"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_token_blacklist_is_revoked"), table_name="token_blacklist")
    op.drop_index(op.f("ix_token_blacklist_token_type"), table_name="token_blacklist")
    op.drop_index(op.f("ix_token_blacklist_jti"), table_name="token_blacklist")
    op.drop_index(op.f("ix_token_blacklist_user_id"), table_name="token_blacklist")
    op.drop_index(op.f("ix_token_blacklist_id"), table_name="token_blacklist")
    op.drop_table("token_blacklist")
