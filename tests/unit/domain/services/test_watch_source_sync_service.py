from __future__ import annotations

from backend.domain.services.watch_source_sync_service import WatchSourceSyncServiceInterface


class TestWatchSourceSyncServiceInterface:
    def test_abstract_method_names(self):
        assert {"sync_sources", "add_watch_source"} <= set(
            WatchSourceSyncServiceInterface.__abstractmethods__
        )

    def test_cannot_be_instantiated(self):
        try:
            WatchSourceSyncServiceInterface()  # type: ignore[abstract]
            raised = False
        except TypeError:
            raised = True
        assert raised is True
