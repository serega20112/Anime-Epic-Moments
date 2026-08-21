from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from backend.application.dto import SaveViewingSessionCommand
from backend.application.use_cases.watch.session.save_viewing_session import (
    SaveViewingSessionUseCase,
)


@pytest.mark.unit
class TestSaveViewingSessionUseCase:
    """Юнит-тесты сохранения позиции просмотра."""

    async def test_persists_session_object(self):
        """Что тестируем: передачу корректной ViewingSession в репозиторий.
        Что передаём: команду сохранения сессии и замоканный кэш.
        Что ожидаем: результат успешен, сессия сохранена, кэш инвалидирован.
        """
        watch_repo = AsyncMock()
        profile_cache = AsyncMock()
        watch_repo.upsert_session.return_value = "saved"
        use_case = SaveViewingSessionUseCase(watch_repo, AsyncMock(), profile_cache)

        result = await use_case.execute(
            SaveViewingSessionCommand(
                user_id=1,
                anime_id=7,
                episode=2,
                watch_source_id=3,
                position_seconds=15.5,
                volume=0.4,
                quality_label="1080",
                is_paused=False,
            )
        )

        assert result.ok is True
        assert result.data == "saved"
        session = watch_repo.upsert_session.await_args.args[0]
        assert session.user_id == 1
        assert session.watch_source_id == 3
        assert session.position_seconds == 15.5
        profile_cache.invalidate_overview.assert_awaited_once_with(1)

    async def test_rejects_invalid_payload(self):
        """Что тестируем: отказ при отсутствии episode/watch_source_id.
        Что передаём: команду без episode.
        Что ожидаем: результат failure со статусом 400, репозиторий не вызывается.
        """
        watch_repo = AsyncMock()
        use_case = SaveViewingSessionUseCase(watch_repo, AsyncMock())

        result = await use_case.execute(
            SaveViewingSessionCommand(
                user_id=1,
                anime_id=7,
                episode=None,
                watch_source_id=None,
            )
        )

        assert result.ok is False
        assert result.status_code == 400
        watch_repo.upsert_session.assert_not_awaited()
