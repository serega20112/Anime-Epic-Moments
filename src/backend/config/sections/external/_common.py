"""Служебные helper'и секции: отсечение плейсхолдерных значений секретов."""

from __future__ import annotations

_PLACEHOLDER_PREFIXES = ("your-", "change-me", "xxx")


def _clean_secret(value: str | None) -> str | None:
    """Вернуть секрет или None, если вместо него стоит заглушка.

    Args:
        value: Сырое значение из окружения.

    Returns:
        str | None: Очищенное значение или None для пустой строки и заглушки.
    """
    text = str(value or "").strip()
    if not text:
        return None
    lowered = text.lower()
    return None if lowered.startswith(_PLACEHOLDER_PREFIXES) else text
