"""Политика подтверждения адреса почты."""

from __future__ import annotations

from secrets import randbelow

VERIFICATION_CODE_LENGTH = 6
DEFAULT_THEME = "neon"
ALLOWED_THEMES = frozenset({"neon", "dark", "light", "rose"})


def generate_verification_code() -> str:
    """Сгенерировать шестизначный код подтверждения почты.

    Returns:
        str: Код ровно из шести цифр с ведущими нулями.
    """
    return f"{randbelow(10**VERIFICATION_CODE_LENGTH):0{VERIFICATION_CODE_LENGTH}d}"


def normalize_theme(value: str | None) -> str:
    """Привести тему оформления к допустимой.

    Args:
        value: Исходное название темы либо None.

    Returns:
        str: Тема из допустимого набора либо нейтральная по умолчанию.
    """
    normalized = str(value or "").strip().lower()
    return normalized if normalized in ALLOWED_THEMES else DEFAULT_THEME
