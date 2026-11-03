"""Привязка аккаунта к Google и флаг подтверждения почты.

Добавляет пользователям столбец ``google_subject`` (уникальный стабильный
идентификатор аккаунта Google) и ``email_verified`` для входа и привязки по
ID-токену. Оба столбца необязательны и не ломают существующие учётные записи.

Revision ID: 4b9e2c7a1d55
Revises: 7f3c1a9d4b28
Create Date: 2026-11-02 12:30:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "4b9e2c7a1d55"
down_revision = "7f3c1a9d4b28"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Добавить столбцы привязки Google и подтверждения почты."""
    op.add_column(
        "users",
        sa.Column("google_subject", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("email_verified", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.create_index(
        op.f("ix_users_google_subject"), "users", ["google_subject"], unique=True
    )


def downgrade() -> None:
    """Удалить индекс и столбцы привязки Google и подтверждения почты."""
    op.drop_index(op.f("ix_users_google_subject"), table_name="users")
    op.drop_column("users", "email_verified")
    op.drop_column("users", "google_subject")
