from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from backend.application.dto.notification import (
    MarkAllNotificationsReadCommand,
    MarkNotificationReadCommand,
    NotificationsQuery,
)
from backend.application.use_cases.notification import (
    GetUserNotificationsUseCase,
    MarkAllNotificationsReadUseCase,
    MarkNotificationReadUseCase,
)
from backend.domain import Notification
from tests.support.fakes import FakeUnitOfWork


def _notification(notification_id: int, actor_id: int | None) -> Notification:
    """Собрать уведомление с указанным идентификатором и автором."""
    return Notification(
        id=notification_id,
        user_id=7,
        kind="highlight_like",
        text="Ваш хайлайт оценили",
        actor_user_id=actor_id,
        highlight_id=3,
    )


@pytest.mark.unit
class TestGetUserNotificationsUseCase:
    """Юнит-тесты чтения страницы уведомлений."""

    async def test_pages_items_and_resolves_actor_names(self):
        """Что тестируем: нарезку страницы уведомлений и имена авторов.
        Что передаём: два уведомления и зрителя с одной страницей по одному.
        Что ожидаем: первое уведомление, total два, unread и имя автора подставлены.
        """
        notification_repository = AsyncMock()
        notification_repository.get_by_user.return_value = [
            _notification(1, 42),
            _notification(2, None),
        ]
        notification_repository.count_unread.return_value = 1
        user_repository = AsyncMock()
        user_repository.get_by_ids.return_value = [SimpleNamespace(id=42, username="alice")]
        uow = FakeUnitOfWork(
            NotificationRepository=notification_repository,
            UserRepository=user_repository,
        )

        page = await GetUserNotificationsUseCase(uow).execute(
            NotificationsQuery(user_id=7, page=1, per_page=1)
        )

        assert [item.id for item in page.items] == [1]
        assert page.total == 2
        assert page.unread_count == 1
        assert page.actor_names == {42: "alice"}
        notification_repository.get_by_user.assert_awaited_once_with(7, limit=1)

    async def test_skips_actor_lookup_without_actors(self):
        """Что тестируем: отсутствие запроса имён, когда авторов нет.
        Что передаём: одно уведомление без автора события.
        Что ожидаем: карта имён пуста, репозиторий пользователей не вызывается.
        """
        notification_repository = AsyncMock()
        notification_repository.get_by_user.return_value = [_notification(1, None)]
        notification_repository.count_unread.return_value = 0
        user_repository = AsyncMock()
        uow = FakeUnitOfWork(
            NotificationRepository=notification_repository,
            UserRepository=user_repository,
        )

        page = await GetUserNotificationsUseCase(uow).execute(
            NotificationsQuery(user_id=7, page=1, per_page=10)
        )

        assert page.actor_names == {}
        user_repository.get_by_ids.assert_not_awaited()


@pytest.mark.unit
class TestMarkReadUseCases:
    """Юнит-тесты отметки уведомлений прочитанными."""

    async def test_mark_read_returns_changed_count(self):
        """Что тестируем: отметку одного уведомления прочитанным.
        Что передаём: владельца и идентификатор уведомления.
        Что ожидаем: число изменений проброшено из репозитория.
        """
        repository = AsyncMock()
        repository.mark_read.return_value = 1
        uow = FakeUnitOfWork(NotificationRepository=repository)

        marked = await MarkNotificationReadUseCase(uow).execute(
            MarkNotificationReadCommand(user_id=7, notification_id=5)
        )

        assert marked == 1
        repository.mark_read.assert_awaited_once_with(7, 5)

    async def test_mark_all_read_returns_changed_count(self):
        """Что тестируем: массовую отметку прочтения.
        Что передаём: владельца уведомлений.
        Что ожидаем: число изменений проброшено из репозитория.
        """
        repository = AsyncMock()
        repository.mark_all_read.return_value = 3
        uow = FakeUnitOfWork(NotificationRepository=repository)

        marked = await MarkAllNotificationsReadUseCase(uow).execute(
            MarkAllNotificationsReadCommand(user_id=7)
        )

        assert marked == 3
        repository.mark_all_read.assert_awaited_once_with(7)
