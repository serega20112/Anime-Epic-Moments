from __future__ import annotations

from backend.domain.services.highlight_dashboard_cache import HighlightDashboardCacheInterface


class TestHighlightDashboardCacheInterface:
    def test_abstract_method_names(self):
        assert {"get_dashboard", "set_dashboard", "invalidate"} <= set(
            HighlightDashboardCacheInterface.__abstractmethods__
        )

    def test_cannot_be_instantiated(self):
        try:
            HighlightDashboardCacheInterface()  # type: ignore[abstract]
            raised = False
        except TypeError:
            raised = True
        assert raised is True