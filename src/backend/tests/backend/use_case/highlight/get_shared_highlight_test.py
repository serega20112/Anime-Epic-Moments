from __future__ import annotations

from unittest.mock import Mock

from src.backend.use_case.highlight.get_shared_highlight import GetSharedHighlightUseCase


def test_get_shared_highlight_use_case_increments_views_and_builds_dashboard(monkeypatch):
    """Проверяем, что GetSharedHighlightUseCase увеличивает просмотры и собирает shared-dashboard."""
    repo = Mock()
    repo.increment_views.return_value = "highlight"
    use_case = GetSharedHighlightUseCase(repo, Mock())
    monkeypatch.setattr(use_case, "_build_dashboard", lambda **kwargs: kwargs)

    result = use_case.execute(highlight_id=5, viewer_user_id=3)

    repo.increment_views.assert_called_once_with(5)
    assert result["highlights"] == ["highlight"]
    assert result["sort_by"] == "recent"
    assert result["viewer_user_id"] == 3
