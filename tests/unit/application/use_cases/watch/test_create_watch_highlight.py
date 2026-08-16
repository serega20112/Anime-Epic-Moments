from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from backend.application.dto import CreateWatchHighlightCommand
from backend.application.use_cases.watch.create_watch_highlight import (
    CreateWatchHighlightUseCase,
)


@pytest.mark.unit
class TestCreateWatchHighlightUseCase:
    """Юнит-тесты создания хайлайта с playback context."""

    async def test_creates_highlight_and_context(self):
        """Что тестируем: создание хайлайта и сохранение playback context.
        Что передаём: команду со всеми полями и замоканный create_highlight.
        Что ожидаем: хайлайт создан, контекст сохранен со ссылкой на него.
        """
        create_highlight_use_case = AsyncMock()
        create_highlight_use_case.execute.return_value = SimpleNamespace(
            ok=True, data=SimpleNamespace(id=33, error=None, status_code=201)
        )
        watch_repo = AsyncMock()
        use_case = CreateWatchHighlightUseCase(create_highlight_use_case, watch_repo, AsyncMock())

        result = await use_case.execute(
            CreateWatchHighlightCommand(
                user_id=1,
                anime_id=7,
                episode=2,
                title="best scene",
                category="бой",
                start_timestamp=10.0,
                end_timestamp=20.0,
                description="great",
                is_spoiler=False,
                emotion="hype",
                watch_source_id=5,
                translation_id=6,
            )
        )

        assert result.ok is True
        assert result.status_code == 201
        assert result.data.id == 33
        create_highlight_use_case.execute.assert_awaited_once()
        context = watch_repo.add_highlight_context.await_args.args[0]
        assert context.highlight_id == 33
        assert context.watch_source_id == 5
        assert context.translation_id == 6
        assert context.title == "best scene"

    async def test_rejects_invalid_payload(self):
        """Что тестируем: отказ при неполном payload.
        Что передаём: команду без episode и watch_source_id.
        Что ожидаем: результат failure со статусом 400, create_highlight не вызывается.
        """
        create_highlight_use_case = AsyncMock()
        watch_repo = AsyncMock()
        use_case = CreateWatchHighlightUseCase(create_highlight_use_case, watch_repo, AsyncMock())

        result = await use_case.execute(
            CreateWatchHighlightCommand(
                user_id=1,
                anime_id=7,
                episode=None,
                title="best scene",
                category="бой",
                start_timestamp=None,
                end_timestamp=None,
                description="great",
                is_spoiler=False,
                emotion="hype",
                watch_source_id=None,
                translation_id=None,
            )
        )

        assert result.ok is False
        assert result.status_code == 400
        create_highlight_use_case.execute.assert_not_awaited()
