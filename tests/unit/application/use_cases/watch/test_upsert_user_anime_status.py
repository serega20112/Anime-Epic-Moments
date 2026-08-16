from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from backend.application.dto import UpsertUserAnimeStatusCommand
from backend.application.use_cases import UpsertUserAnimeStatusUseCase


@pytest.mark.unit
class TestUpsertUserAnimeStatusUseCase:
    """Юнит-тесты создания/обновления статуса просмотра аниме."""

    async def test_persists_domain_object(self):
        """Что тестируем: передачу корректного UserAnimeStatus в репозиторий.
        Что передаём: команду со статусом и замоканный кэш.
        Что ожидаем: результат успешен, статус сохранен, кэш инвалидирован.
        """
        watch_repo = AsyncMock()
        profile_cache = AsyncMock()
        watch_repo.upsert_status.return_value = "saved"
        use_case = UpsertUserAnimeStatusUseCase(watch_repo, AsyncMock(), profile_cache)

        result = await use_case.execute(
            UpsertUserAnimeStatusCommand(user_id=1, anime_id=9, status="watching")
        )

        assert result.ok is True
        assert result.data == "saved"
        status = watch_repo.upsert_status.await_args.args[0]
        assert status.user_id == 1
        assert status.anime_id == 9
        assert status.status == "watching"
        profile_cache.invalidate_overview.assert_awaited_once_with(1)

    async def test_rejects_empty_status(self):
        """Что тестируем: отказ при пустом статусе.
        Что передаём: status из пробелов.
        Что ожидаем: результат failure со статусом 400, репозиторий не вызывается.
        """
        watch_repo = AsyncMock()
        use_case = UpsertUserAnimeStatusUseCase(watch_repo, AsyncMock())

        result = await use_case.execute(
            UpsertUserAnimeStatusCommand(user_id=1, anime_id=9, status="   ")
        )

        assert result.ok is False
        assert result.status_code == 400
        watch_repo.upsert_status.assert_not_awaited()
