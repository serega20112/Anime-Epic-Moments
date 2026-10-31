"""Преобразователи запросов для команд поддержки."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from backend.application.dto import CreateSupportTicketCommand
from backend.domain import normalize_support_channel
from backend.domain.policies.user_credentials_policy import normalize_email, normalize_username

PAGE_URL_MAX_LENGTH = 500


def map_create_support_ticket_command(
    form: Mapping[str, Any],
    *,
    user_id: int | None,
    user_email: str | None = None,
    user_username: str | None = None,
) -> CreateSupportTicketCommand:
    """Собрать команду создания обращения в поддержку из данных формы.

    Args:
        form: Сырые поля HTML-формы обращения.
        user_id: Идентификатор автора либо None для гостя.
        user_email: Почта автора из сессии, если пользователь войдён.
        user_username: Имя автора из сессии, если пользователь войдён.

    Returns:
        CreateSupportTicketCommand: Команда с нормализованными полями обращения.
    """
    email = normalize_email(user_email if user_id is not None else form.get("email"))
    username = normalize_username(user_username if user_id is not None else form.get("username"))
    return CreateSupportTicketCommand(
        user_id=user_id,
        email=email,
        username=username,
        subject=str(form.get("subject") or "").strip(),
        message=str(form.get("message") or "").strip(),
        channel=normalize_support_channel(form.get("channel")),
        page_url=_normalize_page_url(form.get("page_url")),
    )


def _normalize_page_url(value: str | None) -> str | None:
    """Ограничить адрес страницы допустимой длиной.

    Args:
        value: Сырое значение адреса страницы.

    Returns:
        str | None: Адрес страницы либо None при пустом значении.
    """
    normalized = str(value or "").strip()[:PAGE_URL_MAX_LENGTH]
    return normalized or None
