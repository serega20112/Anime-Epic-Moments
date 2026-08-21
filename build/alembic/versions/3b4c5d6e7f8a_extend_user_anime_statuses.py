"""extend user anime statuses for diary

Revision ID: 3b4c5d6e7f8a
Revises: 2f3a4b5c6d7e
Create Date: 2026-08-16 12:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "3b4c5d6e7f8a"
down_revision = "2f3a4b5c6d7e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("user_anime_statuses", sa.Column("current_episode", sa.Integer(), nullable=True))
    op.add_column("user_anime_statuses", sa.Column("started_at", sa.DateTime(), nullable=True))
    op.add_column("user_anime_statuses", sa.Column("completed_at", sa.DateTime(), nullable=True))
    op.add_column("user_anime_statuses", sa.Column("last_watched_at", sa.DateTime(), nullable=True))
    op.add_column("user_anime_statuses", sa.Column("rating", sa.Float(), nullable=True))
    op.add_column("user_anime_statuses", sa.Column("note", sa.String(length=500), nullable=True))


def downgrade() -> None:
    op.drop_column("user_anime_statuses", "note")
    op.drop_column("user_anime_statuses", "rating")
    op.drop_column("user_anime_statuses", "last_watched_at")
    op.drop_column("user_anime_statuses", "completed_at")
    op.drop_column("user_anime_statuses", "started_at")
    op.drop_column("user_anime_statuses", "current_episode")