"""Порт хранилища уведомлений пользователя."""

from abc import ABC, abstractmethod

from backend.domain.entities.notification.notification import Notification


class NotificationRepository(ABC):
    """Хранилище уведомлений центра уведомлений мобильного клиента."""

    @abstractmethod
    async def add(self, notification: Notification) -> Notification:
        """Сохранить новое уведомление и вернуть его с идентификатором."""

    @abstractmethod
    async def get_by_user(self, user_id: int, limit: int = 20) -> list[Notification]:
        """Вернуть уведомления получателя в порядке новых сначала."""

    @abstractmethod
    async def count_unread(self, user_id: int) -> int:
        """Вернуть число непрочитанных уведомлений получателя."""

    @abstractmethod
    async def mark_read(self, user_id: int, notification_id: int) -> int:
        """Пометить одно уведомление прочитанным и вернуть число изменений."""

    @abstractmethod
    async def mark_all_read(self, user_id: int) -> int:
        """Пометить все уведомления получателя прочитанными и вернуть число изменений."""
