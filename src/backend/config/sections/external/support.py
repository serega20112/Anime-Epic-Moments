"""Настройки канала поддержки.

Telegram-бот (токен, адрес API и чаты администраторов), почтовый ящик получателя
тикетов и параметры SMTP для отправки писем.
"""

from __future__ import annotations

import os


def telegram_support_bot_token() -> str | None:
    """Вернуть токен Telegram-бота поддержки."""
    return os.getenv("TELEGRAM_SUPPORT_BOT_TOKEN")


def telegram_support_api_url() -> str:
    """Вернуть базовый адрес Telegram Bot API."""
    return os.getenv("TELEGRAM_SUPPORT_API_URL", "https://api.telegram.org")


def telegram_support_admin_chat_ids() -> list[str]:
    """Вернуть идентификаторы чатов администраторов для оповещений поддержки."""
    return [
        item.strip()
        for item in os.getenv("TELEGRAM_SUPPORT_ADMIN_CHAT_IDS", "").split(",")
        if item.strip()
    ]


def support_email_to() -> list[str]:
    """Вернуть адреса получателей писем поддержки."""
    return [item.strip() for item in os.getenv("SUPPORT_EMAIL_TO", "").split(",") if item.strip()]


def smtp_host() -> str | None:
    """Вернуть хост SMTP-сервера."""
    return os.getenv("SMTP_HOST")


def smtp_port() -> int:
    """Вернуть порт SMTP-сервера."""
    return int(os.getenv("SMTP_PORT", "587"))


def smtp_username() -> str | None:
    """Вернуть имя пользователя SMTP."""
    return os.getenv("SMTP_USERNAME")


def smtp_password() -> str | None:
    """Вернуть пароль SMTP."""
    return os.getenv("SMTP_PASSWORD")


def smtp_from_email() -> str | None:
    """Вернуть адрес отправителя писем поддержки."""
    return os.getenv("SMTP_FROM_EMAIL")


def smtp_use_tls() -> bool:
    """Вернуть, включает ли SMTP шифрование через STARTTLS."""
    return os.getenv("SMTP_USE_TLS", "1") == "1"
