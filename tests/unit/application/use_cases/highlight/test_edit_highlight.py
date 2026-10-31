from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from backend.application.dto import EditHighlightCommand
from backend.application.use_cases.highlight.crud.edit_highlight import EditHighlightUseCase
from backend.domain import Highlight
from tests.support.fakes import FakeUnitOfWork


def _highlight(owner_id: int) -> Highlight:
    """Собрать существующий хайлайт указанного автора."""
    highlight = Highlight(
        user_id=owner_id,
        anime_id=1,
        episode=1,
        start_timestamp=1.0,
        end_timestamp=2.0,
        title="old",
        category="драма",
        description="old desc",
    )
    highlight.id = 1
    return highlight


def _use_case(repository: AsyncMock) -> tuple:
    """Собрать сценарий правки с двойником репозитория."""
    recommendation_service = AsyncMock()
    dashboard_cache = AsyncMock()
    profile_cache = AsyncMock()
    uow = FakeUnitOfWork(HighlightRepository=repository)
    use_case = EditHighlightUseCase(uow, recommendation_service, dashboard_cache, profile_cache)
    return use_case, uow, recommendation_service, dashboard_cache, profile_cache


def _command(**overrides) -> EditHighlightCommand:
    """Собрать команду правки хайлайта с переопределёнными полями."""
    fields = {
        "highlight_id": 1,
        "user_id": 7,
        "episode": 3,
        "start_timestamp": 10.0,
        "end_timestamp": 20.0,
        "title": "new title",
        "category": "бой",
        "description": "new desc",
        "is_spoiler": True,
        "emotion": "hype",
    }
    fields.update(overrides)
    return EditHighlightCommand(**fields)


@pytest.mark.unit
class TestEditHighlightUseCase:
    """Юнит-тесты редактирования хайлайта."""

    async def test_updates_highlight_and_invalidates_caches(self):
        """Что тестируем: обновление полей и инвалидацию зависимых кэшей.
        Что передаём: существующий хайлайт и команду его автора.
        Что ожидаем: поля обновлены, транзакция зафиксирована, кэши очищены.
        """
        repository = AsyncMock()
        highlight = _highlight(7)
        repository.get_by_id.return_value = highlight
        repository.update.side_effect = lambda item: item
        use_case, uow, recommendations, dashboard_cache, profile_cache = _use_case(repository)

        result = await use_case.execute(_command())

        assert result.ok is True
        assert result.data is highlight
        assert highlight.episode == 3
        assert highlight.title == "new title"
        assert highlight.category == "бой"
        assert highlight.is_spoiler is True
        assert uow.commits == 1
        repository.update.assert_awaited_once_with(highlight)
        recommendations.invalidate_user.assert_awaited_once_with(7)
        dashboard_cache.invalidate_public.assert_awaited_once()
        profile_cache.invalidate_user.assert_awaited_once_with(7, include_ai_summary=True)

    async def test_returns_forbidden_for_foreign_highlight(self):
        """Что тестируем: проверку автора при редактировании.
        Что передаём: хайлайт автора 7 и команду от пользователя 8.
        Что ожидаем: статус 403, обновление и инвалидация не выполняются.
        """
        repository = AsyncMock()
        repository.get_by_id.return_value = _highlight(7)
        use_case, _uow, recommendations, dashboard_cache, _profile_cache = _use_case(repository)

        result = await use_case.execute(_command(user_id=8))

        assert result.ok is False
        assert result.status_code == 403
        repository.update.assert_not_awaited()
        recommendations.invalidate_user.assert_not_awaited()
        dashboard_cache.invalidate_public.assert_not_awaited()

    @pytest.mark.parametrize("description", ["мат", "спам"])
    async def test_rejects_blocked_description(self, description):
        """Что тестируем: отказ при запрещённом контенте в title/description.
        Что передаём: description с запрещённым словом и существующий хайлайт.
        Что ожидаем: статус 400, обновление не выполняется.
        """
        repository = AsyncMock()
        repository.get_by_id.return_value = _highlight(7)
        use_case, _uow, _recommendations, _dashboard_cache, _profile_cache = _use_case(repository)

        result = await use_case.execute(
            _command(title="blocked", category="драма", description=description, emotion=None)
        )

        assert result.ok is False
        assert result.status_code == 400
        repository.update.assert_not_awaited()

    async def test_returns_failure_for_missing_item(self):
        """Что тестируем: отказ при отсутствующем хайлайте.
        Что передаём: get_by_id=None.
        Что ожидаем: статус 404, обновление не выполняется.
        """
        repository = AsyncMock()
        repository.get_by_id.return_value = None
        use_case, _uow, _recommendations, _dashboard_cache, _profile_cache = _use_case(repository)

        result = await use_case.execute(_command(highlight_id=999))

        assert result.ok is False
        assert result.status_code == 404
        repository.update.assert_not_awaited()

    async def test_returns_failure_for_invalid_window(self):
        """Что тестируем: отказ домена при некорректном интервале хайлайта.
        Что передаём: начало фрагмента позже его конца.
        Что ожидаем: статус 400 из ошибки валидации, обновление не выполняется.
        """
        repository = AsyncMock()
        repository.get_by_id.return_value = _highlight(7)
        use_case, _uow, _recommendations, _dashboard_cache, _profile_cache = _use_case(repository)

        result = await use_case.execute(_command(start_timestamp=30.0, end_timestamp=20.0))

        assert result.ok is False
        assert result.status_code == 400
        repository.update.assert_not_awaited()
