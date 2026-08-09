from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import Mock

from backend.application.use_cases.highlight.get_highlight_feed import GetHighlightFeedUseCase


def test_get_highlight_feed_use_case_collects_public_and_personal_sections(monkeypatch):
    """Проверяем, что GetHighlightFeedUseCase собирает popular, recent, liked и from_favorites секции в один feed."""
    card = SimpleNamespace(anime_id=11, anime_title="Initial D", category="бой")
    repo = Mock()
    repo.get_public_top.return_value = ["popular"]
    repo.get_public_recent.return_value = ["recent"]
    repo.get_liked_by_user.return_value = ["liked"]
    repo.get_from_anime_ids.return_value = ["favorite"]
    repo.get_profile_summary.return_value = SimpleNamespace(highlight_count=1, like_count=2, saved_count=3)
    repo.get_recent_activity.return_value = [SimpleNamespace(action="like")]
    favorite_repo = Mock()
    favorite_repo.get_by_user.return_value = [SimpleNamespace(anime_id=11)]
    use_case = GetHighlightFeedUseCase(repo, Mock(), favorite_repo)

    monkeypatch.setattr(
        use_case,
        "_build_dashboard",
        lambda **kwargs: SimpleNamespace(items=[card for _ in kwargs["highlights"]]),
    )

    result = use_case.execute(viewer_user_id=7, category="бой")

    repo.get_public_top.assert_called_once_with(12)
    repo.get_public_recent.assert_called_once_with(12)
    repo.get_liked_by_user.assert_called_once_with(7, limit=12)
    repo.get_from_anime_ids.assert_called_once_with([11], limit=12)
    assert result.popular_items == [card]
    assert result.recent_items == [card]
    assert result.liked_items == [card]
    assert result.from_favorites_items == [card]
    assert result.profile.saved_count == 3
