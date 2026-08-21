"""Правила учётных данных пользователя: нормализация и формат email/username.

Единый источник правил формата: агрегат User и presentation-мапперы обязаны
использовать функции отсюда, чтобы правила не расходились между слоями.
"""

from __future__ import annotations

import re

EMAIL_PATTERN = r"^[\w\.-]+@[\w\.-]+\.\w+$"
EMAIL_MAX_LENGTH = 254
USERNAME_MIN_LENGTH = 3
USERNAME_MAX_LENGTH = 20


async def normalize_email(value: object) -> str:
    """Приводит email к каноническому виду: обрезка пробелов и lower-case."""
    return str(value or "").strip().lower()


async def is_valid_email_format(email: str) -> bool:
    """Проверяет соответствие email доменному формату (без проверки длины формы)."""
    return bool(re.match(EMAIL_PATTERN, email or ""))


async def normalize_username(value: object) -> str:
    """Схлопывает внутренние пробелы и обрезает края (для отображения/тикетов)."""
    return " ".join(str(value or "").strip().split())
