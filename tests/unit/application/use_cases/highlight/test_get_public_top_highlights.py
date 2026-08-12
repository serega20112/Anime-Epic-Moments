from __future__ import annotations

from unittest.mock import Mock

from backend.application.use_cases import (
    GetPublicTopHighlightsUseCase,
)


def test_get_public_top_highlights_uses_popularity_or_recency_query(monkeypatch):
    """Проверяем, что GetPublicTopHighlightsUseCase выбирает get_public_top или get_public_recent в зависимости от sort_by."""
    repo = Mock()
    repo.get_public_top.return_value = ["highlight-1"]
    repo.get_public_recent.return_value = ["highlight-2"]
    use_case = GetPublicTopHighlightsUseCase(repo, Mock())
    monkeypatch.setattr(use_case, "_build_dashboard", lambda **kwargs: kwargs)

    popular_result = use_case.execute(limit=12, emotion="funny", include_spoilers=True, sort_by="popular")
    recent_result = use_case.execute(limit=9, include_spoilers=False, sort_by="recent")

    repo.get_public_top.assert_called_once_with(12)
    repo.get_public_recent.assert_called_once_with(9)
    assert popular_result["highlights"] == ["highlight-1"]
    assert popular_result["sort_by"] == "popular"
    assert recent_result["highlights"] == ["highlight-2"]
    assert recent_result["sort_by"] == "recent"


def test_get_public_top_highlights_uses_sort_in_cache_key():
    """Проверяем, что GetPublicTopHighlightsUseCase передает sort_by в кэш публичного дашборда."""
    repo = Mock()
    cache = Mock()
    cache.get_public.return_value = None
    use_case = GetPublicTopHighlightsUseCase(repo, Mock(), highlight_dashboard_cache=cache)
    use_case._build_dashboard = Mock(return_value="dashboard")

    use_case.execute(limit=6, sort_by="recent", include_spoilers=False)

    cache.get_public.assert_called_once_with(
        limit=6,
        anime_id=None,
        emotion=None,
        category=None,
        sort_by="recent",
        created_date=None,
        query=None,
        include_spoilers=False,
    )
    cache.set_public.assert_called_once_with(
        limit=6,
        anime_id=None,
        emotion=None,
        category=None,
        sort_by="recent",
        created_date=None,
        query=None,
        include_spoilers=False,
        value="dashboard",
    )
