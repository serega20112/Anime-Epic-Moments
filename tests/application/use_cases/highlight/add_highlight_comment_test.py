from __future__ import annotations

from unittest.mock import Mock

from backend.application.use_cases.highlight.add_highlight_comment import AddHighlightCommentUseCase


def test_add_highlight_comment_use_case_validates_content_and_invalidates_cache():
    """Проверяем, что AddHighlightCommentUseCase сохраняет комментарий и инвалидирует публичный кэш."""
    repo = Mock()
    repo.add_comment.return_value = "comment"
    dashboard_cache = Mock()
    use_case = AddHighlightCommentUseCase(repo, dashboard_cache)

    result = use_case.execute(highlight_id=5, user_id=7, content="great scene")

    repo.add_comment.assert_called_once_with(highlight_id=5, user_id=7, content="great scene")
    dashboard_cache.invalidate_public.assert_called_once()
    assert result == "comment"
