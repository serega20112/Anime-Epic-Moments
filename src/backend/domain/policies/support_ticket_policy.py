"""Правила создания тикета поддержки.

Нормализация и проверки формата живут здесь, чтобы правила не расходились
между слоем приложения и агрегатом. Правила email и username переиспользуются
из политики учётных данных пользователя.
"""

from __future__ import annotations

from urllib.parse import urlparse

from backend.domain.entities.support.channel import parse_support_channel
from backend.domain.exceptions import ValidationError
from backend.domain.policies.user_credentials_policy import (
    EMAIL_MAX_LENGTH,
    is_valid_email_format,
    normalize_email,
    normalize_username,
)

SUBJECT_MIN_LENGTH = 4
SUBJECT_MAX_LENGTH = 120
MESSAGE_MIN_LENGTH = 10
MESSAGE_MAX_LENGTH = 4000
USERNAME_MAX_LENGTH = 40
PAGE_URL_MAX_LENGTH = 500


def normalize_support_email(value: object) -> str:
    """Нормализовать email тикета.

    Args:
        value: Исходное значение.

    Returns:
        str: Email в нижнем регистре без лишних пробелов.
    """
    return normalize_email(value)


def normalize_support_username(value: object) -> str:
    """Нормализовать имя пользователя тикета.

    Args:
        value: Исходное значение.

    Returns:
        str: Имя со схлопнутыми пробелами.
    """
    return normalize_username(value)


def normalize_page_url(value: object) -> str | None:
    """Нормализовать адрес страницы, с которой отправлен тикет.

    Args:
        value: Исходное значение.

    Returns:
        str | None: Адрес либо None для пустого значения.

    Raises:
        ValidationError: Адрес длиннее 500 символов либо использует схему,
            отличную от http/https.
    """
    candidate = str(value or "").strip()
    if not candidate:
        return None
    if len(candidate) > PAGE_URL_MAX_LENGTH:
        raise ValidationError("Адрес страницы не должен превышать 500 символов")
    if candidate.startswith("/"):
        return candidate
    parsed = urlparse(candidate)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValidationError("Укажите корректный адрес страницы")
    return candidate


def validate_support_email(email: str) -> None:
    """Проверить email тикета.

    Args:
        email: Нормализованный email.

    Raises:
        ValidationError: Email пуст, слишком длинный или не соответствует
            доменному формату.
    """
    if not email:
        raise ValidationError("Укажите email для ответа")
    if len(email) > EMAIL_MAX_LENGTH:
        raise ValidationError(f"Email не должен превышать {EMAIL_MAX_LENGTH} символов")
    if not is_valid_email_format(email):
        raise ValidationError("Некорректный email")


def validate_support_username(username: str) -> None:
    """Проверить имя пользователя тикета.

    Args:
        username: Нормализованное имя.

    Raises:
        ValidationError: Имя пустое или длиннее 40 символов.
    """
    if not username:
        raise ValidationError("Укажите имя пользователя")
    if len(username) > USERNAME_MAX_LENGTH:
        raise ValidationError("Имя пользователя не должно превышать 40 символов")


def validate_support_subject(subject: str) -> None:
    """Проверить тему тикета.

    Args:
        subject: Тема обращения.

    Raises:
        ValidationError: Тема короче 4 или длиннее 120 символов.
    """
    if len(subject) < SUBJECT_MIN_LENGTH:
        raise ValidationError("Тема должна содержать минимум 4 символа")
    if len(subject) > SUBJECT_MAX_LENGTH:
        raise ValidationError("Тема не должна превышать 120 символов")


def validate_support_message(message: str) -> None:
    """Проверить текст обращения.

    Args:
        message: Текст обращения.

    Raises:
        ValidationError: Текст короче 10 или длиннее 4000 символов.
    """
    if len(message) < MESSAGE_MIN_LENGTH:
        raise ValidationError("Сообщение должно содержать минимум 10 символов")
    if len(message) > MESSAGE_MAX_LENGTH:
        raise ValidationError("Сообщение не должно превышать 4000 символов")


def validate_support_channel(channel: str) -> str:
    """Проверить и нормализовать канал доставки тикета.

    Args:
        channel: Название канала.

    Returns:
        str: Нормализованное имя канала.

    Raises:
        ValidationError: Канал не поддерживается.
    """
    normalized = parse_support_channel(channel)
    if not normalized:
        raise ValidationError("Канал доставки должен быть telegram или email")
    return normalized
