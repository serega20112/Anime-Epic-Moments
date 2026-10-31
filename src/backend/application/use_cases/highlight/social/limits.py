"""Общие ограничения выборок социальных действий с хайлайтами."""

from __future__ import annotations

MAX_LIMIT = 100


def clamp_limit(limit: int) -> int:
    """Ограничить размер выборки допустимым диапазоном.

    Args:
        limit: Запрошенное число записей.

    Returns:
        int: Число записей в диапазоне от 1 до 100.
    """
    return max(min(int(limit), MAX_LIMIT), 1)
