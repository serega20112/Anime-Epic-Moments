from __future__ import annotations

from unittest.mock import Mock

import pytest

from backend.application.use_cases.highlight.edit_highlight import EditHighlightUseCase


def test_edit_highlight_use_case_updates_highlight_and_invalidates_cache():
    """Проверяем, что edit_highlight обновляет title и category и инвалидирует зависимые кэши."""
    highlight = Mock(user_id=7)
    repo = Mock(get_by_id=Mock(return_value=highlight), update=Mock(return_value=highlight))
    recommendation_service = Mock()
    dashboard_cache = Mock()
    use_case = EditHighlightUseCase(repo, recommendation_service, dashboard_cache)

    result = use_case.execute(
        highlight_id=1,
        episode=3,
        start_timestamp=10.0,
        end_timestamp=20.0,
        title="new title",
        category="бой",
        description="new desc",
        is_spoiler=True,
        emotion="hype",
    )

    highlight.edit.assert_called_once_with(
        start_timestamp=10.0,
        end_timestamp=20.0,
        title="new title",
        category="бой",
        description="new desc",
        is_spoiler=True,
        emotion="hype",
    )
    assert highlight.episode == 3
    repo.update.assert_called_once_with(highlight)
    recommendation_service.invalidate_user.assert_called_once_with(7)
    dashboard_cache.invalidate_public.assert_called_once()
    assert result is highlight


@pytest.mark.parametrize("description", ["мат", "спам"])
def test_edit_highlight_use_case_rejects_blocked_description(description):
    """Проверяем, что edit_highlight не пропускает запрещенный контент в title/description."""
    repo = Mock(get_by_id=Mock(return_value=Mock()))
    use_case = EditHighlightUseCase(repo, Mock(), Mock())

    with pytest.raises(ValueError):
        use_case.execute(
            highlight_id=1,
            episode=1,
            start_timestamp=10.0,
            end_timestamp=20.0,
            title="blocked",
            category="драма",
            description=description,
            is_spoiler=False,
        )
