from __future__ import annotations

from backend.application.interface.repositories.highlight_repository import HighlightRepository


class TestHighlightRepository:
    def test_abstract_method_names(self):
        assert {
            "add",
            "update",
            "delete",
            "get_by_id",
            "get_by_user",
            "get_by_users",
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
        } <= set(HighlightRepository.__abstractmethods__)

    def test_cannot_be_instantiated(self):
        try:
            HighlightRepository()  # type: ignore[abstract]
            raised = False
        except TypeError:
            raised = True
        assert raised is True
