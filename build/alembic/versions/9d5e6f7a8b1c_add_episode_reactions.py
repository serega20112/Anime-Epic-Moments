"""add episode reactions

Revision ID: 9d5e6f7a8b1c
Revises: c10c4f4d4ef8
Create Date: 2026-08-16 10:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "9d5e6f7a8b1c"
down_revision = "c10c4f4d4ef8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "episode_reactions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("anime_id", sa.Integer(), nullable=False),
        sa.Column("episode", sa.Integer(), nullable=False),
        sa.Column("reaction_type", sa.String(), nullable=False),
        sa.Column("timestamp", sa.Float(), nullable=False, server_default=sa.text("0.0")),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "user_id",
            "anime_id",
            "episode",
            name="uq_episode_reaction",
        ),
    )
    op.create_index(
        "ix_episode_reactions_user_id",
        "episode_reactions",
        ["user_id"],
    )
    op.create_index(
        "ix_episode_reactions_anime_id_episode",
        "episode_reactions",
        ["anime_id", "episode"],
    )


def downgrade() -> None:
    op.drop_index("ix_episode_reactions_anime_id_episode", table_name="episode_reactions")
    op.drop_index("ix_episode_reactions_user_id", table_name="episode_reactions")
    op.drop_table("episode_reactions")

