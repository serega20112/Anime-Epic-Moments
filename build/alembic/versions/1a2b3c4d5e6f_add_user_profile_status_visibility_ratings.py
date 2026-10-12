"""add user profile status visibility ratings and level

Revision ID: 1a2b3c4d5e6f
Revises: 0f7f86580f46
Create Date: 2026-09-01 12:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "1a2b3c4d5e6f"
down_revision = "0f7f86580f46"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("status", sa.String(length=80), nullable=True))
    op.add_column(
        "users",
        sa.Column("show_watch_activity", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.add_column(
        "users",
        sa.Column("show_recent_episodes", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.alter_column(
        "viewing_sessions",
        "watch_source_id",
        existing_type=sa.Integer(),
        nullable=True,
    )
    op.create_table(
        "user_anime_ratings",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("anime_id", sa.Integer(), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("rated_at", sa.DateTime(), nullable=True),
        sa.UniqueConstraint("user_id", "anime_id", name="uq_user_anime_ratings_user_anime"),
    )
    op.create_index(
        op.f("ix_user_anime_ratings_user_id"),
        "user_anime_ratings",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_user_anime_ratings_user_id"), table_name="user_anime_ratings")
    op.drop_table("user_anime_ratings")
    op.alter_column(
        "viewing_sessions",
        "watch_source_id",
        existing_type=sa.Integer(),
        nullable=False,
    )
    op.drop_column("users", "show_recent_episodes")
    op.drop_column("users", "show_watch_activity")
    op.drop_column("users", "status")
