from __future__ import annotations

from unittest.mock import Mock

from src.backend.use_case.highlight.set_highlight_like import SetHighlightLikeUseCase


def test_set_highlight_like_use_case_updates_like_and_invalidates_cache():
    """Проверяем, что SetHighlightLikeUseCase переключает лайк и инвалидирует публичный кэш."""
    repo = Mock()
    repo.set_like.return_value = "highlight"
    dashboard_cache = Mock()
    use_case = SetHighlightLikeUseCase(repo, dashboard_cache)

    result = use_case.execute(highlight_id=4, user_id=3, liked=True)

    repo.set_like.assert_called_once_with(highlight_id=4, user_id=3, liked=True)
    dashboard_cache.invalidate_public.assert_called_once()
    assert result == "highlight"
