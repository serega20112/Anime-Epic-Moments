from __future__ import annotations

from backend.domain.repositories.watch_repository import WatchRepository


class TestWatchRepository:
    def test_abstract_method_names(self):
        assert {
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
        } <= set(WatchRepository.__abstractmethods__)

    def test_cannot_be_instantiated(self):
        try:
            WatchRepository()  # type: ignore[abstract]
            raised = False
        except TypeError:
            raised = True
        assert raised is True
