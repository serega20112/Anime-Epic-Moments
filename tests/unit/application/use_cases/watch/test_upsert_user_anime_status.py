from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from backend.application.dto import UpsertUserAnimeStatusCommand
from backend.application.use_cases import UpsertUserAnimeStatusUseCase
from backend.domain import UserAnimeStatus
from tests.support.fakes import FakeUnitOfWork


def _use_case(repository: AsyncMock) -> tuple:
    """Собрать сценарий upsert статуса с двойниками репозитория и кэша."""
    profile_cache = AsyncMock()
    uow = FakeUnitOfWork(WatchRepository=repository)
    return UpsertUserAnimeStatusUseCase(uow, profile_cache), uow, repository, profile_cache


@pytest.mark.unit
class TestUpsertUserAnimeStatusUseCase:
    """Юнит-тесты сохранения статуса просмотра аниме."""

    async def test_saves_status_and_invalidates_profile_cache(self):
        """Что тестируем: запись статуса и инвалидацию кэша профиля после коммита.
        Что передаём: команду с статусом и лишними пробелами.
        Что ожидаем: сущность сохранена, кэш очищен, транзакция зафиксирована.
        """
        repository = AsyncMock()
        repository.upsert_status.side_effect = lambda item: item
        use_case, uow, _repository, profile_cache = _use_case(repository)

        result = await use_case.execute(
            UpsertUserAnimeStatusCommand(user_id=4, anime_id=7, status="  watching ")
        )

        assert result.ok is True
        assert result.data.status == "watching"
        assert uow.commits == 1
        saved = repository.upsert_status.await_args.args[0]
        assert isinstance(saved, UserAnimeStatus)
        profile_cache.invalidate_overview.assert_awaited_once_with(4)

    async def test_rejects_empty_status(self):
        """Что тестируем: отказ при пустом статусе.
        Что передаём: статус из пробелов.
        Что ожидаем: статус 400, репозиторий и кэш не затронуты.
        """
        repository = AsyncMock()
        use_case, _uow, _repository, profile_cache = _use_case(repository)

        result = await use_case.execute(
            UpsertUserAnimeStatusCommand(user_id=4, anime_id=7, status=" ")
        )

        assert result.ok is False
        assert result.status_code == 400
        assert result.error == "status_required"
        repository.upsert_status.assert_not_awaited()
        profile_cache.invalidate_overview.assert_not_awaited()
