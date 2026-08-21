from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from backend.application.dto import CreateHighlightCommand
from backend.application.use_cases.highlight.crud.create_highlight import CreateHighlightUseCase


@pytest.mark.unit
class TestCreateHighlightUseCase:
    """Юнит-тесты создания хайлайта."""

    @pytest.mark.parametrize(
        ("user_id", "highlights_this_hour", "should_invalidate"),
        [(1, 0, True), (None, 0, False)],
    )
    async def test_persists_highlight_and_invalidates_cache(
        self, user_id, highlights_this_hour, should_invalidate
    ):
        """Что тестируем: сохранение хайлайта и инвалидацию только для авторизованного.
        Что передаём: user_id/количество за час.
        Что ожидаем: repo.add вызван, инвалидация рекомендаций по флагу.
        """
        repo = AsyncMock()
        repo.add.side_effect = lambda highlight: highlight
        recommendation_service = AsyncMock()
        use_case = CreateHighlightUseCase(repo, AsyncMock(), recommendation_service)

        result = await use_case.execute(
            CreateHighlightCommand(
                user_id=user_id,
                anime_id=18,
                episode=1,
                start_timestamp=10.0,
                end_timestamp=25.0,
                description="epic drift",
                is_spoiler=False,
                emotion="hype",
                highlights_this_hour=highlights_this_hour,
            )
        )

        assert result.ok is True
        assert result.status_code == 201
        assert result.data.description == "epic drift"
        repo.add.assert_awaited_once()
        assert len(recommendation_service.invalidate_user.await_args_list) == int(should_invalidate)

    @pytest.mark.parametrize("description", ["мат", "спам"])
    async def test_rejects_blocked_content(self, description):
        """Что тестируем: отказ при запрещенном контенте в описании.
        Что передаём: description с banned-словом.
        Что ожидаем: результат failure со статусом 400, repo.add не вызывается.
        """
        repo = AsyncMock()
        use_case = CreateHighlightUseCase(repo, AsyncMock())

        result = await use_case.execute(
            CreateHighlightCommand(
                user_id=1,
                anime_id=18,
                episode=1,
                start_timestamp=10.0,
                end_timestamp=20.0,
                description=description,
            )
        )

        assert result.ok is False
        assert result.status_code == 400
        repo.add.assert_not_awaited()

    async def test_limits_guest_highlights_per_hour(self):
        """Что тестируем: лимит гостя на количество хайлайтов в час.
        Что передаём: user_id=None и highlights_this_hour=5.
        Что ожидаем: результат failure со статусом 403, repo.add не вызывается.
        """
        repo = AsyncMock()
        use_case = CreateHighlightUseCase(repo, AsyncMock())

        result = await use_case.execute(
            CreateHighlightCommand(
                user_id=None,
                anime_id=18,
                episode=1,
                start_timestamp=10.0,
                end_timestamp=25.0,
                highlights_this_hour=5,
            )
        )

        assert result.ok is False
        assert result.status_code == 403
        repo.add.assert_not_awaited()
