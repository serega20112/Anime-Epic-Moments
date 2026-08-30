from __future__ import annotations

from backend.application.interface.services.watch_source_service import (
    WatchSourceSyncServiceInterface,
)
from backend.application.services.watch_source_service import WatchSourceSyncService


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


class _FakeProvider:
    def __init__(self, name: str):
        self.provider_name = name


class TestHentaiRouting:
    def test_is_adult_detects_hentai_genres(self):
        assert WatchSourceSyncService._is_adult(["Action", "Hentai"]) is True
        assert WatchSourceSyncService._is_adult(["Ecchi"]) is True
        assert WatchSourceSyncService._is_adult(["Adventure", "Fantasy"]) is False
        assert WatchSourceSyncService._is_adult(None) is False
        assert WatchSourceSyncService._is_adult([]) is False

    def test_filtered_providers_adult_restricts_to_eporner_only(self):
        service = WatchSourceSyncService.__new__(WatchSourceSyncService)
        service.providers = [
            _FakeProvider("Kodik"),
            _FakeProvider("Eporner"),
            _FakeProvider("Hanime"),
            _FakeProvider("YouTube"),
        ]
        adult = [p.provider_name for p in service._filtered_providers(True)]
        assert adult == ["Eporner"]

    def test_filtered_providers_normal_keeps_all(self):
        service = WatchSourceSyncService.__new__(WatchSourceSyncService)
        service.providers = [_FakeProvider("Kodik"), _FakeProvider("Eporner")]
        names = [p.provider_name for p in service._filtered_providers(False)]
        assert names == ["Kodik", "Eporner"]
