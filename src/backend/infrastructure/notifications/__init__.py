"""Внешние уведомления: почтовые рассылки и Telegram-оповещения.

Подпакет отвечает за доставку сообщений вовне и ничего не знает о HTTP-слое:

- `email` — письма подтверждения адреса, сброса пароля и тикеты поддержки;
- `telegram` — оповещение администраторов поддержки.

Каждая реализация закрывает порт из `backend.application.interface.services`, поэтому
use case'ы зависят от интерфейса, а не от SMTP или Telegram.
"""

from __future__ import annotations

from .telegram import TelegramSupportNotifier

__all__ = [
    "TelegramSupportNotifier",
]
