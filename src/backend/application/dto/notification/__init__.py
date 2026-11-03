"""DTO уведомлений мобильного клиента."""

from backend.application.dto.notification.mark_read_commands import (
    MarkAllNotificationsReadCommand,
    MarkNotificationReadCommand,
)
from backend.application.dto.notification.notifications_query import NotificationsQuery

__all__ = [
    "MarkAllNotificationsReadCommand",
    "MarkNotificationReadCommand",
    "NotificationsQuery",
]
