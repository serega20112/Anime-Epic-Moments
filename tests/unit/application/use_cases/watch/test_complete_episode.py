from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from backend.application.dto import CompleteEpisodeCommand
from backend.application.use_cases import CompleteEpisodeUseCase
from backend.domain import UserAnimeStatus
from tests.support.fakes import FakeUnitOfWork


def _use_case(repository: AsyncMock) -> tuple:
    """Собрать сценарий завершения серии с двойниками репозитория и кэша."""
    profile_cache = AsyncMock()
    uow = FakeUnitOfWork(WatchRepository=repository)
    return CompleteEpisodeUseCase(uow, profile_cache), uow, repository, profile_cache


@pytest.mark.unit
class TestCompleteEpisodeUseCase:
    """Юнит-тесты отметки просмотренной серии."""

    async def test_records_completion_and_invalidates_profile_cache(self):
        """Что тестируем: продвижение прогресса и инвалидацию кэша профиля.
        Что передаём: команду завершения второй серии.
        Что ожидаем: прогресс записан, кэш очищен, транзакция зафиксирована.
        """
        repository = AsyncMock()
        repository.record_episode_completion.return_value = UserAnimeStatus(
            user_id=4, anime_id=7, status="watching", current_episode=3
        )
        use_case, uow, _repository, profile_cache = _use_case(repository)

        result = await use_case.execute(CompleteEpisodeCommand(user_id=4, anime_id=7, episode=2))

        assert result.ok is True
        assert result.data.current_episode == 3
        assert uow.commits == 1
        repository.record_episode_completion.assert_awaited_once_with(
            user_id=4, anime_id=7, episode=2
        )
        profile_cache.invalidate_overview.assert_awaited_once_with(4)

    @pytest.mark.parametrize("episode", [None, 0])
    async def test_rejects_invalid_episode(self, episode):
        """Что тестируем: отказ при некорректном номере серии.
        Что передаём: episode=None и episode=0.
        Что ожидаем: статус 400, прогресс не записывается, кэш не трогается.
        """
        repository = AsyncMock()
        use_case, _uow, _repository, profile_cache = _use_case(repository)

        result = await use_case.execute(
            CompleteEpisodeCommand(user_id=4, anime_id=7, episode=episode)
        )

        assert result.ok is False
        assert result.status_code == 400
        assert result.error == "invalid_episode"
        repository.record_episode_completion.assert_not_awaited()
        profile_cache.invalidate_overview.assert_not_awaited()
