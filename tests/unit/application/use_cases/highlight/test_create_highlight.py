from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from backend.application.dto import CreateHighlightCommand
from backend.application.use_cases.highlight.crud.create_highlight import CreateHighlightUseCase
from tests.support.fakes import FakeUnitOfWork


def _command(**overrides) -> CreateHighlightCommand:
    """Собрать команду создания хайлайта с переопределёнными полями."""
    fields = {
        "user_id": 1,
        "anime_id": 18,
        "episode": 1,
        "start_timestamp": 10.0,
        "end_timestamp": 25.0,
        "description": "epic drift",
        "is_spoiler": False,
        "emotion": "hype",
        "highlights_this_hour": 0,
    }
    fields.update(overrides)
    return CreateHighlightCommand(**fields)


@pytest.mark.unit
class TestCreateHighlightUseCase:
    """Юнит-тесты создания хайлайта."""

    async def test_persists_highlight_and_invalidates_owner_caches(self):
        """Что тестируем: сохранение хайлайта и инвалидацию кэшей автора.
        Что передаём: команду авторизованного пользователя.
        Что ожидаем: транзакция зафиксирована, рекомендации и кэши очищены.
        """
        repository = AsyncMock()
        repository.add.side_effect = lambda highlight: highlight
        recommendation_service = AsyncMock()
        dashboard_cache = AsyncMock()
        profile_cache = AsyncMock()
        uow = FakeUnitOfWork(HighlightRepository=repository)
        use_case = CreateHighlightUseCase(
            uow, recommendation_service, dashboard_cache, profile_cache
        )

        result = await use_case.execute(_command())

        assert result.ok is True
        assert result.status_code == 201
        assert result.data.description == "epic drift"
        assert uow.commits == 1
        repository.add.assert_awaited_once()
        recommendation_service.invalidate_user.assert_awaited_once_with(1)
        dashboard_cache.invalidate_public.assert_awaited_once()
        profile_cache.invalidate_user.assert_awaited_once_with(1, include_ai_summary=True)

    async def test_invalidates_only_public_cache_for_guest(self):
        """Что тестируем: инвалидацию гостевого хайлайта.
        Что передаём: команду с user_id=None.
        Что ожидаем: публичный кэш очищен, кэши автора не затрагиваются.
        """
        repository = AsyncMock()
        repository.add.side_effect = lambda highlight: highlight
        recommendation_service = AsyncMock()
        dashboard_cache = AsyncMock()
        profile_cache = AsyncMock()
        use_case = CreateHighlightUseCase(
            FakeUnitOfWork(HighlightRepository=repository),
            recommendation_service,
            dashboard_cache,
            profile_cache,
        )

        result = await use_case.execute(_command(user_id=None))

        assert result.ok is True
        dashboard_cache.invalidate_public.assert_awaited_once()
        recommendation_service.invalidate_user.assert_not_awaited()
        profile_cache.invalidate_user.assert_not_awaited()

    @pytest.mark.parametrize("description", ["мат", "спам"])
    async def test_rejects_blocked_content(self, description):
        """Что тестируем: отказ при запрещённом контенте в описании.
        Что передаём: description с запрещённым словом.
        Что ожидаем: статус 400, хайлайт не сохранён.
        """
        repository = AsyncMock()
        use_case = CreateHighlightUseCase(
            FakeUnitOfWork(HighlightRepository=repository), AsyncMock(), AsyncMock(), AsyncMock()
        )

        result = await use_case.execute(
            _command(end_timestamp=20.0, description=description, highlights_this_hour=0)
        )

        assert result.ok is False
        assert result.status_code == 400
        repository.add.assert_not_awaited()

    async def test_limits_guest_highlights_per_hour(self):
        """Что тестируем: лимит гостя на количество хайлайтов в час.
        Что передаём: user_id=None и highlights_this_hour=5.
        Что ожидаем: статус 403, хайлайт не сохранён.
        """
        repository = AsyncMock()
        use_case = CreateHighlightUseCase(
            FakeUnitOfWork(HighlightRepository=repository), AsyncMock(), AsyncMock(), AsyncMock()
        )

        result = await use_case.execute(_command(user_id=None, highlights_this_hour=5))

        assert result.ok is False
        assert result.status_code == 403
        repository.add.assert_not_awaited()
