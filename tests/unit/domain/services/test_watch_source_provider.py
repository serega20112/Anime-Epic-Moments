from __future__ import annotations

from backend.domain.services.watch_source_provider import WatchSourceProviderInterface


class TestWatchSourceProviderInterface:
    def test_abstract_method_names(self):
        assert {"get_sources", "close"} <= set(WatchSourceProviderInterface.__abstractmethods__)

    def test_cannot_be_instantiated(self):
        try:
            WatchSourceProviderInterface()  # type: ignore[abstract]
            raised = False
        except TypeError:
            raised = True
        assert raised is True
