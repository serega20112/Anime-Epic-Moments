from __future__ import annotations

from backend.domain.services.profile_overview_cache import ProfileOverviewCacheInterface


class TestProfileOverviewCacheInterface:
    def test_abstract_method_names(self):
        assert {
            "get_overview",
            "set_overview",
            "get_ai_summary",
            "set_ai_summary",
            "invalidate",
        } <= set(ProfileOverviewCacheInterface.__abstractmethods__)

    def test_cannot_be_instantiated(self):
        try:
            ProfileOverviewCacheInterface()  # type: ignore[abstract]
            raised = False
        except TypeError:
            raised = True
        assert raised is True
