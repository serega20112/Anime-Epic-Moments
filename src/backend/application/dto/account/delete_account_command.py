"""Команда удаления аккаунта пользователя."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DeleteAccountCommand:
    """Намерение безвозвратно удалить собственный аккаунт.

    Attributes:
        user_id: Идентификатор пользователя, удаляемого аккаунта.
    """

    user_id: int
