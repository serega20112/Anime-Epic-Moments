"""Доменные правила каналов доставки тикетов поддержки."""

from __future__ import annotations

SUPPORT_CHANNELS: frozenset[str] = frozenset({"telegram", "email"})
DEFAULT_SUPPORT_CHANNEL = "telegram"


def parse_support_channel(value: str | None) -> str | None:
    """Разобрать канал доставки без подстановки значения по умолчанию.

    Args:
        value: Название канала.

    Returns:
        str | None: Канал в нижнем регистре либо None, если он неизвестен.
    """
    normalized = str(value or "").strip().lower()
    return normalized if normalized in SUPPORT_CHANNELS else None


def normalize_support_channel(value: str | None, *, default: str = DEFAULT_SUPPORT_CHANNEL) -> str:
    """Нормализовать канал поддержки с подстановкой значения по умолчанию.

    Args:
        value: Название канала.
        default: Канал, используемый для неизвестного значения.

    Returns:
        str: Известный канал (``telegram`` или ``email``).
    """
    return parse_support_channel(value) or default


def is_support_channel(value: str | None) -> bool:
    """Проверить, поддерживается ли канал.

    Args:
        value: Проверяемое название канала.

    Returns:
        bool: True, если канал поддерживается.
    """
    return parse_support_channel(value) is not None
