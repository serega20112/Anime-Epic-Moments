"""Обращение пользователя в поддержку."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CreateSupportTicketCommand:
    """Команда создания обращения в поддержку.

    Attributes:
        user_id: Идентификатор вошедшего пользователя либо None для гостя.
        email: Адрес для ответа.
        username: Имя пользователя или подпись гостя.
        subject: Тема обращения.
        message: Текст обращения.
        channel: Канал, из которого пришло обращение.
        page_url: Адрес страницы, на которой возникла проблема.
    """

    user_id: int | None
    email: str
    username: str
    subject: str
    message: str
    channel: str
    page_url: str | None = None
