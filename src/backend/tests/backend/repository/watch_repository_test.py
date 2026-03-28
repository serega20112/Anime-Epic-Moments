from __future__ import annotations

import pytest

from src.backend.repository.watch_repository import WatchRepository


def test_watch_repository_is_abstract_and_declares_expected_methods():
    """Проверяем, что контракт WatchRepository остается абстрактным и полным."""
    assert WatchRepository.__abstractmethods__ == {
        "get_status",
        "upsert_status",
        "get_translations",
        "add_translation",
        "get_sources",
        "add_source",
        "get_session",
        "upsert_session",
        "add_highlight_context",
        "get_highlight_contexts",
        "get_watched_anime_stats",
        "get_viewing_heatmap",
        "add_anime_comment",
        "get_anime_comments",
        "set_anime_comment_like",
    }

    with pytest.raises(TypeError):
        WatchRepository()
