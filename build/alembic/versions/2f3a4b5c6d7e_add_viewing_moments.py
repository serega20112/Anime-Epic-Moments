"""add viewing moments

Revision ID: 2f3a4b5c6d7e
Revises: 9d5e6f7a8b1c
Create Date: 2026-08-16 11:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "2f3a4b5c6d7e"
down_revision = "9d5e6f7a8b1c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "viewing_moments",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("anime_id", sa.Integer(), nullable=False),
        sa.Column("episode", sa.Integer(), nullable=False),
        sa.Column("timestamp", sa.Float(), nullable=False, server_default=sa.text("0.0")),
        sa.Column(
            "watch_source_id",
            sa.Integer(),
            sa.ForeignKey("watch_sources.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("caption", sa.String(length=200), nullable=True),
        sa.Column("sticker", sa.String(length=40), nullable=True),
        sa.Column("screenshot_url", sa.String(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )
    op.create_index("ix_viewing_moments_user_id", "viewing_moments", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_viewing_moments_user_id", table_name="viewing_moments")
    op.drop_table("viewing_moments")