from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from backend.application.dto import DeleteHighlightCommand
from backend.application.use_cases.highlight.crud.delete_highlight import DeleteHighlightUseCase
from backend.domain import Highlight
from tests.support.fakes import FakeUnitOfWork


def _highlight(owner_id: int) -> Highlight:
    """Собрать хайлайт указанного автора с идентификатором 55."""
    highlight = Highlight(
        user_id=owner_id,
        anime_id=1,
        episode=1,
        start_timestamp=1.0,
        end_timestamp=2.0,
        description="desc",
    )
    highlight.id = 55
    return highlight


def _use_case(repository: AsyncMock) -> tuple:
    """Собрать сценарий удаления с двойником репозитория."""
    recommendation_service = AsyncMock()
    dashboard_cache = AsyncMock()
    profile_cache = AsyncMock()
    uow = FakeUnitOfWork(HighlightRepository=repository)
    use_case = DeleteHighlightUseCase(uow, recommendation_service, dashboard_cache, profile_cache)
    return use_case, uow, recommendation_service, dashboard_cache, profile_cache


@pytest.mark.unit
class TestDeleteHighlightUseCase:
    """Юнит-тесты удаления хайлайта."""

    async def test_removes_highlight_and_invalidates_caches(self):
        """Что тестируем: удаление найденного хайлайта и очистку кэшей.
        Что передаём: существующий хайлайт и команду его автора.
        Что ожидаем: транзакция зафиксирована, рекомендации и кэши очищены.
        """
        repository = AsyncMock()
        repository.get_by_id.return_value = _highlight(8)
        use_case, uow, recommendations, dashboard_cache, profile_cache = _use_case(repository)

        result = await use_case.execute(DeleteHighlightCommand(highlight_id=55, user_id=8))

        assert result.ok is True
        assert result.status_code == 204
        assert uow.commits == 1
        repository.delete.assert_awaited_once_with(55)
        recommendations.invalidate_user.assert_awaited_once_with(8)
        dashboard_cache.invalidate_public.assert_awaited_once()
        profile_cache.invalidate_user.assert_awaited_once_with(8, include_ai_summary=True)

    async def test_returns_forbidden_for_foreign_highlight(self):
        """Что тестируем: проверку автора при удалении.
        Что передаём: хайлайт автора 8 и команду от пользователя 9.
        Что ожидаем: статус 403, удаление и инвалидация не выполняются.
        """
        repository = AsyncMock()
        repository.get_by_id.return_value = _highlight(8)
        use_case, uow, recommendations, dashboard_cache, profile_cache = _use_case(repository)

        result = await use_case.execute(DeleteHighlightCommand(highlight_id=55, user_id=9))

        assert result.ok is False
        assert result.status_code == 403
        assert uow.commits == 1
        repository.delete.assert_not_awaited()
        recommendations.invalidate_user.assert_not_awaited()
        dashboard_cache.invalidate_public.assert_not_awaited()
        profile_cache.invalidate_user.assert_not_awaited()

    @pytest.mark.parametrize("highlight_id", [1, 77])
    async def test_returns_failure_for_missing_item(self, highlight_id):
        """Что тестируем: корректный ответ при отсутствии хайлайта.
        Что передаём: get_by_id=None.
        Что ожидаем: статус 404, удаление не выполняется.
        """
        repository = AsyncMock()
        repository.get_by_id.return_value = None
        use_case, _uow, _recommendations, dashboard_cache, _profile_cache = _use_case(repository)

        result = await use_case.execute(
            DeleteHighlightCommand(highlight_id=highlight_id, user_id=8)
        )

        assert result.ok is False
        assert result.status_code == 404
        repository.delete.assert_not_awaited()
        dashboard_cache.invalidate_public.assert_not_awaited()
