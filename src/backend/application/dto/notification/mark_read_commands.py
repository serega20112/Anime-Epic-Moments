"""Команды отметки уведомлений прочитанными."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MarkNotificationReadCommand:
    """Команда отметить одно уведомление прочитанным.

    Attributes:
        user_id: Идентификатор получателя — владельца уведомления.
        notification_id: Идентификатор уведомления.
    """

    user_id: int
    notification_id: int


@dataclass(frozen=True, slots=True)
class MarkAllNotificationsReadCommand:
    """Команда отметить все уведомления получателя прочитанными.

    Attributes:
        user_id: Идентификатор получателя уведомлений.
    """

    user_id: int
