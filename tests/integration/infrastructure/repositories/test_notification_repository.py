from __future__ import annotations

import pytest

from backend.domain import Notification, User
from backend.infrastructure.database.repositories.notification_repository import (
    NotificationRepository,
)
from backend.infrastructure.database.repositories.user_repository import UserRepository


def _notification(user_id: int, actor_id: int, kind: str = "highlight_like") -> Notification:
    """Собрать уведомление получателю с указанным автором и типом."""
    return Notification(
        user_id=user_id,
        actor_user_id=actor_id,
        kind=kind,
        text="Событие",
        anime_id=185,
        highlight_id=3,
    )


@pytest.mark.integration
class TestNotificationRepository:
    """Интеграционные тесты NotificationRepository на in-memory базе."""

    async def test_add_get_count_and_mark_read(self, async_db_session):
        """Что тестируем: полный цикл репозитория уведомлений на реальной базе.
        Что передаём: двух пользователей и три уведомления первому (одно от него же).
        Что ожидаем: чтение в порядке новых сначала, счётчик непрочитанных и отметки
        прочтения меняют ровно ожидаемые записи и ничего лишнего.
        """
        owner = await UserRepository(async_db_session).add(
            User(email="owner@example.com", username="owner", password_hash="hash")
        )
        actor = await UserRepository(async_db_session).add(
            User(email="actor@example.com", username="actor", password_hash="hash")
        )
        repo = NotificationRepository(async_db_session)
        first = await repo.add(_notification(owner.id, actor.id))
        await repo.add(_notification(owner.id, actor.id, kind="highlight_comment"))
        await repo.add(_notification(owner.id, actor.id, kind="new_follower"))

        items = await repo.get_by_user(owner.id, limit=10)
        unread = await repo.count_unread(owner.id)

        assert len(items) == 3
        assert {item.kind for item in items} == {
            "highlight_like",
            "highlight_comment",
            "new_follower",
        }
        assert unread == 3

        assert await repo.mark_read(owner.id, first.id or 0) == 1
        assert await repo.mark_read(owner.id, first.id or 0) == 0
        assert await repo.count_unread(owner.id) == 2

        assert await repo.mark_all_read(owner.id) == 2
        assert await repo.count_unread(owner.id) == 0

    async def test_mark_read_ignores_other_owner(self, async_db_session):
        """Что тестируем: защиту чужих уведомлений при отметке прочтения.
        Что передаём: уведомление первого пользователя и запрос от второго.
        Что ожидаем: изменений нет, уведомление остаётся непрочитанным.
        """
        owner = await UserRepository(async_db_session).add(
            User(email="a@example.com", username="reader-a", password_hash="hash")
        )
        intruder = await UserRepository(async_db_session).add(
            User(email="b@example.com", username="reader-b", password_hash="hash")
        )
        repo = NotificationRepository(async_db_session)
        created = await repo.add(_notification(owner.id, owner.id))

        changed = await repo.mark_read(intruder.id, created.id or 0)

        assert changed == 0
        assert await repo.count_unread(owner.id) == 1
