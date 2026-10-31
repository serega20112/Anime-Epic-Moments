"""Сборщики данных формы для страницы поддержки."""

from __future__ import annotations

from backend.application.dto import CreateSupportTicketCommand
from backend.domain import normalize_support_channel
from backend.domain.policies.user_credentials_policy import normalize_email, normalize_username

PAGE_URL_MAX_LENGTH = 500


def build_support_form_data(
    *,
    command: CreateSupportTicketCommand,
    user_email: str | None = None,
    user_username: str | None = None,
) -> dict[str, str]:
    """Собрать заполненные данные формы из команды для повторного показа.

    Args:
        command: Команда, которая не прошла валидацию.
        user_email: Почта автора из сессии, если пользователь войдён.
        user_username: Имя автора из сессии, если пользователь войдён.

    Returns:
        dict[str, str]: Поля формы для повторной отрисовки.
    """
    return {
        "email": normalize_email(user_email) if user_email else command.email,
        "username": normalize_username(user_username) if user_username else command.username,
        "subject": str(command.subject or "").strip(),
        "message": str(command.message or "").strip(),
        "channel": command.channel,
        "page_url": normalize_page_url(command.page_url),
    }


def build_default_support_form(
    *,
    user_email: str | None = None,
    user_username: str | None = None,
    channel_param: object = None,
    page_param: object = None,
) -> dict[str, str]:
    """Собрать данные формы по умолчанию из текущего пользователя и параметров запроса.

    Args:
        user_email: Почта пользователя сессии либо None для гостя.
        user_username: Имя пользователя сессии либо None для гостя.
        channel_param: Значение параметра ``channel`` из адреса страницы.
        page_param: Значение параметра ``page`` из адреса страницы.

    Returns:
        dict[str, str]: Предзаполненные поля формы обращения.
    """
    return {
        "email": normalize_email(user_email),
        "username": normalize_username(user_username),
        "subject": "",
        "message": "",
        "channel": normalize_support_channel(channel_param),
        "page_url": normalize_page_url(page_param),
    }


def normalize_page_url(value: object) -> str:
    """Нормализовать адрес страницы с обрезкой до допустимой длины.

    Args:
        value: Сырое значение адреса страницы.

    Returns:
        str: Адрес страницы без пробелов и не длиннее лимита.
    """
    return str(value or "").strip()[:PAGE_URL_MAX_LENGTH]
