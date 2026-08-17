from __future__ import annotations

from backend.domain.services.watch_source_provider import WatchSourceProviderInterface


class TestWatchSourceProviderInterface:
    def test_abstract_method_names(self):
        assert {"is_enabled", "search_sources"} <= set(
            WatchSourceProviderInterface.__abstractmethods__
        )

    def test_cannot_be_instantiated(self):
        try:
            WatchSourceProviderInterface()  # type: ignore[abstract]
            raised = False
        except TypeError:
            raised = True
        assert raised is True
