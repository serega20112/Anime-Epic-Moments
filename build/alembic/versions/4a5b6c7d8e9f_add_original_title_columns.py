"""add original title columns to snapshot tables

Revision ID: 4a5b6c7d8e9f
Revises: 3b4c5d6e7f8a
Create Date: 2026-08-31 12:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "4a5b6c7d8e9f"
down_revision = "3b4c5d6e7f8a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("favorites", sa.Column("original_title", sa.String(), nullable=True))
    op.add_column(
        "anime_collection_items",
        sa.Column("original_title", sa.String(), nullable=True),
    )
    op.add_column(
        "highlight_contexts",
        sa.Column("original_title", sa.String(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("highlight_contexts", "original_title")
    op.drop_column("anime_collection_items", "original_title")
    op.drop_column("favorites", "original_title")
