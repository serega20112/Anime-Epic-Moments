from __future__ import annotations

import pytest

from backend.domain import User, ViewingMoment
from backend.infrastructure.repositories.moment_repository import MomentRepository
from backend.infrastructure.repositories.user_repository import UserRepository


@pytest.mark.integration
class TestMomentRepository:
    """Интеграционные тесты MomentRepository на in-memory базе."""

    async def test_saves_and_reads_moment(self, async_db_session):
        """Проверяем, что MomentRepository создаёт, обновляет и читает момент."""
        user = await UserRepository(async_db_session).add(
            User(email="moment@example.com", username="momentor", password_hash="hash")
        )
        repo = MomentRepository(async_db_session)

        created = await repo.save_moment(
            ViewingMoment(user_id=user.id, anime_id=7, episode=3, timestamp=12.5)
        )
        loaded = await repo.get_moment(created.id, user.id)

        assert created.id is not None
        assert loaded is not None
        assert loaded.timestamp == 12.5

        updated = await repo.save_moment(
            ViewingMoment(
                user_id=user.id,
                anime_id=7,
                episode=3,
                timestamp=20.0,
                caption="Вау",
                id=created.id,
            )
        )
        assert updated.id == created.id
        assert (await repo.get_moment(created.id, user.id)).caption == "Вау"

    async def test_lists_and_deletes_moments(self, async_db_session):
        """Проверяем, что MomentRepository возвращает список и удаляет момент."""
        user = await UserRepository(async_db_session).add(
            User(email="moment-list@example.com", username="listor", password_hash="hash")
        )
        repo = MomentRepository(async_db_session)
        first = await repo.save_moment(
            ViewingMoment(user_id=user.id, anime_id=7, episode=3, timestamp=1.0)
        )
        await repo.save_moment(ViewingMoment(user_id=user.id, anime_id=7, episode=4, timestamp=2.0))

        moments = await repo.get_moments_by_user(user.id)
        assert len(moments) == 2

        deleted = await repo.delete_moment(first.id, user.id)
        assert deleted is True
        assert len(await repo.get_moments_by_user(user.id)) == 1
        assert await repo.delete_moment(first.id, user.id) is False
