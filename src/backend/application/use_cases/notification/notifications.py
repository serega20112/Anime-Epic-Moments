"""Сценарии центра уведомлений мобильного клиента.

Чтение отдаёт страницу уведомлений вместе с числом непрочитанных, отметка
прочтения меняет состояние по стабильному идентификатору записи. Все решения
о выборке и границах страницы принимаются здесь, маршрут остаётся тонким.
"""

from __future__ import annotations

from backend.application.dto.notification import (
    MarkAllNotificationsReadCommand,
    MarkNotificationReadCommand,
    NotificationsQuery,
)
from backend.application.interface.repositories.notification_repository import (
    NotificationRepository,
)
from backend.application.interface.repositories.user_repository import UserRepository
from backend.application.interface.unit_of_work import UnitOfWorkInterface
from backend.domain import NotificationFeedPage

MAX_PER_PAGE = 50
DEFAULT_PER_PAGE = 20


class GetUserNotificationsUseCase:
    """Возвращает страницу уведомлений получателя и счётчик непрочитанных."""

    def __init__(self, unit_of_work: UnitOfWorkInterface) -> None:
        """Инициализирует сценарий чтения уведомлений.

        Args:
            unit_of_work: Граница транзакции чтения уведомлений.
        """
        self._unit_of_work = unit_of_work

    async def execute(self, query: NotificationsQuery) -> NotificationFeedPage:
        """Собрать страницу уведомлений с навигацией и счётчиком непрочитанных.

        Args:
            query: Получатель, номер и размер страницы.

        Returns:
            NotificationFeedPage: Страница уведомлений.
        """
        page = max(query.page, 1)
        per_page = max(min(query.per_page, MAX_PER_PAGE), 1)
        async with self._unit_of_work as uow:
            repository = uow.repository(NotificationRepository)
            items = await repository.get_by_user(query.user_id, limit=page * per_page)
            unread_count = await repository.count_unread(query.user_id)
            actor_names = await self._load_actor_names(uow, items)
        start = (page - 1) * per_page
        total = len(items)
        return NotificationFeedPage(
            items=items[start : start + per_page],
            page=page,
            per_page=per_page,
            total=total,
            unread_count=unread_count,
            actor_names=actor_names,
        )

    @staticmethod
    async def _load_actor_names(uow: UnitOfWorkInterface, items: list[object]) -> dict[int, str]:
        """Подгрузить имена авторов уведомлений одним запросом.

        Args:
            uow: Граница транзакции с доступом к репозиторию пользователей.
            items: Уведомления, для которых нужны имена авторов.

        Returns:
            dict[int, str]: Имена авторов по идентификатору пользователя.
        """
        actor_ids = sorted(
            {int(item.actor_user_id) for item in items if item.actor_user_id is not None}
        )
        if not actor_ids:
            return {}
        users = await uow.repository(UserRepository).get_by_ids(actor_ids)
        return {user.id: user.username for user in users if user.id is not None}


class MarkNotificationReadUseCase:
    """Отмечает одно уведомление прочитанным."""

    def __init__(self, unit_of_work: UnitOfWorkInterface) -> None:
        """Инициализирует сценарий отметки прочтения.

        Args:
            unit_of_work: Граница транзакции записи прочтения.
        """
        self._unit_of_work = unit_of_work

    async def execute(self, command: MarkNotificationReadCommand) -> int:
        """Пометить уведомление прочитанным для его владельца.

        Args:
            command: Владелец и идентификатор уведомления.

        Returns:
            int: Число изменённых записей; ноль, если уже прочитано или не найдено.
        """
        async with self._unit_of_work as uow:
            marked = await uow.repository(NotificationRepository).mark_read(
                command.user_id, command.notification_id
            )
        return marked


class MarkAllNotificationsReadUseCase:
    """Отмечает все уведомления получателя прочитанными."""

    def __init__(self, unit_of_work: UnitOfWorkInterface) -> None:
        """Инициализирует сценарий массового прочтения.

        Args:
            unit_of_work: Граница транзакции записи прочтения.
        """
        self._unit_of_work = unit_of_work

    async def execute(self, command: MarkAllNotificationsReadCommand) -> int:
        """Пометить все непрочитанные уведомления владельца прочитанными.

        Args:
            command: Владелец уведомлений.

        Returns:
            int: Число изменённых записей.
        """
        async with self._unit_of_work as uow:
            marked = await uow.repository(NotificationRepository).mark_all_read(command.user_id)
        return marked
