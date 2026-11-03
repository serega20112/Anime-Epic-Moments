"""Таблица уведомлений мобильного клиента.

Появляется постоянным хранилищем событий для центра уведомлений: лайк,
комментарий и новый подписчик записываются строкой со стабильным идентификатором
и флагом прочтения, чтобы маршруты ``read``/``read-all`` опирались на него, а не
на производную активность без неизменяемого id.

Revision ID: 7f3c1a9d4b28
Revises: a0c0657fa309
Create Date: 2026-11-02 12:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "7f3c1a9d4b28"
down_revision = "a0c0657fa309"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Создать таблицу уведомлений с индексом по получателю и прочтению."""
    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("actor_user_id", sa.Integer(), nullable=True),
        sa.Column("kind", sa.String(length=32), nullable=False),
        sa.Column("text", sa.String(length=400), nullable=False),
        sa.Column("anime_id", sa.Integer(), nullable=True),
        sa.Column("highlight_id", sa.Integer(), nullable=True),
        sa.Column("is_read", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_notifications_user_id_created_at"),
        "notifications",
        ["user_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    """Удалить индекс и таблицу уведомлений."""
    op.drop_index(op.f("ix_notifications_user_id_created_at"), table_name="notifications")
    op.drop_table("notifications")
