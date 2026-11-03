"""Провайдеры сценариев центра уведомлений мобильного клиента."""

from __future__ import annotations

from dishka import Provider, Scope, provide

from backend.application.interface.unit_of_work import UnitOfWorkInterface
from backend.application.use_cases.notification import (
    GetUserNotificationsUseCase,
    MarkAllNotificationsReadUseCase,
    MarkNotificationReadUseCase,
)


class NotificationUseCaseProvider(Provider):
    """Провайдер сценариев уведомлений."""

    @provide(scope=Scope.REQUEST)
    async def get_user_notifications(
        self, unit_of_work: UnitOfWorkInterface
    ) -> GetUserNotificationsUseCase:
        """Создать сценарий чтения уведомлений."""
        return GetUserNotificationsUseCase(unit_of_work)

    @provide(scope=Scope.REQUEST)
    async def mark_notification_read(
        self, unit_of_work: UnitOfWorkInterface
    ) -> MarkNotificationReadUseCase:
        """Создать сценарий отметки одного уведомления прочитанным."""
        return MarkNotificationReadUseCase(unit_of_work)

    @provide(scope=Scope.REQUEST)
    async def mark_all_notifications_read(
        self, unit_of_work: UnitOfWorkInterface
    ) -> MarkAllNotificationsReadUseCase:
        """Создать сценарий отметки всех уведомлений прочитанными."""
        return MarkAllNotificationsReadUseCase(unit_of_work)
