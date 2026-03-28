from __future__ import annotations

import pytest

from src.backend.repository.highlight_repository import HighlightRepository


def test_highlight_repository_is_abstract_and_declares_expected_methods():
    """Проверяем, что контракт HighlightRepository остается абстрактным и включает social/feed-операции."""
    assert HighlightRepository.__abstractmethods__ == {
        "add",
        "update",
        "delete",
        "get_by_id",
        "get_by_user",
        "get_public_top",
        "get_public_recent",
        "get_by_anime_episode",
        "get_saved_by_user",
        "get_liked_by_user",
        "get_from_anime_ids",
        "set_like",
        "get_likers",
        "add_comment",
        "get_comments",
        "set_saved",
        "get_engagement_map",
        "increment_views",
        "get_profile_summary",
        "get_recent_activity",
    }

    with pytest.raises(TypeError):
        HighlightRepository()
