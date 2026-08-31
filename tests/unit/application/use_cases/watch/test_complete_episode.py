from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from backend.application.dto import CompleteEpisodeCommand
from backend.application.use_cases.watch.session.complete_episode import (
    CompleteEpisodeUseCase,
)


@pytest.mark.unit
class TestCompleteEpisodeUseCase:
    """Юнит-тесты записи события «досмотрено»."""

    async def test_records_completion(self):
        """Что тестируем: передачу корректных аргументов в репозиторий.
        Что передаём: команду завершения эпизода и замоканный кэш.
        Что ожидаем: результат успешен, прогресс записан, кэш инвалидирован.
        """
        watch_repo = AsyncMock()
        profile_cache = AsyncMock()
        watch_repo.record_episode_completion.return_value = "status"
        use_case = CompleteEpisodeUseCase(watch_repo, AsyncMock(), profile_cache)

        result = await use_case.execute(CompleteEpisodeCommand(user_id=1, anime_id=7, episode=3))

        assert result.ok is True
        assert result.data == "status"
        watch_repo.record_episode_completion.assert_awaited_once_with(
            user_id=1,
            anime_id=7,
            episode=3,
        )
        profile_cache.invalidate_overview.assert_awaited_once_with(1)

    async def test_rejects_invalid_episode(self):
        """Что тестируем: отказ при некорректном номере эпизода.
        Что передаём: команду с episode = 0.
        Что ожидаем: результат failure со статусом 400, репозиторий не вызывается.
        """
        watch_repo = AsyncMock()
        use_case = CompleteEpisodeUseCase(watch_repo, AsyncMock())

        result = await use_case.execute(CompleteEpisodeCommand(user_id=1, anime_id=7, episode=0))

        assert result.ok is False
        assert result.status_code == 400
        watch_repo.record_episode_completion.assert_not_awaited()
