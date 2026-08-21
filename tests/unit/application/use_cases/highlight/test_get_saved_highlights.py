from __future__ import annotations

from unittest.mock import Mock

from backend.application.use_cases.highlight.feed.get_saved_highlights import (
    GetSavedHighlightsUseCase,
)


def test_get_saved_highlights_use_case_builds_dashboard_for_current_user(monkeypatch):
    """Проверяем, что GetSavedHighlightsUseCase берет данные из get_saved_by_user и строит дашборд с viewer_user_id и sort_by."""
    repo = Mock()
    repo.get_saved_by_user.return_value = ["highlight"]
    use_case = GetSavedHighlightsUseCase(repo, Mock())
    monkeypatch.setattr(use_case, "_build_dashboard", lambda **kwargs: kwargs)

    result = use_case.execute(user_id=4, category="бой", include_spoilers=False, sort_by="popular")

    repo.get_saved_by_user.assert_called_once_with(4)
    assert result["category"] == "бой"
    assert result["viewer_user_id"] == 4
    assert result["include_spoilers"] is False
    assert result["sort_by"] == "popular"
