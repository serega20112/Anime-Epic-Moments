from __future__ import annotations

from unittest.mock import Mock

from src.backend.use_case.highlight.get_public_top_highlights import (
    GetPublicTopHighlightsUseCase,
)


def test_get_public_top_highlights_uses_public_repo_query(monkeypatch):
    """Проверяем, что GetPublicTopHighlightsUseCase берет данные из get_public_top и собирает dashboard."""
    repo = Mock()
    repo.get_public_top.return_value = ["highlight-1"]
    use_case = GetPublicTopHighlightsUseCase(repo, Mock())
    monkeypatch.setattr(use_case, "_build_dashboard", lambda **kwargs: kwargs)

    result = use_case.execute(limit=12, emotion="funny", include_spoilers=True)

    repo.get_public_top.assert_called_once_with(12)
    assert result["highlights"] == ["highlight-1"]
    assert result["emotion"] == "funny"
    assert result["include_spoilers"] is True
