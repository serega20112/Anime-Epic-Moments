from __future__ import annotations

from unittest.mock import Mock

import pytest

from src.backend.domain.watch.value_object import DiscoveredWatchSource
from src.backend.services.watch_source_sync_service import WatchSourceSyncService


@pytest.mark.parametrize("force_second_call, expected_calls", [(False, 1), (True, 2)])
def test_watch_source_sync_service_caches_empty_provider_results(
    force_second_call,
    expected_calls,
    anime_factory,
):
    """Проверяем, что пустой ответ провайдера повторно не запрашивается до force-refresh."""
    watch_repo = Mock()
    watch_repo.get_sources.return_value = []
    provider = Mock()
    provider.is_enabled.return_value = True
    provider.provider_name = "Kodik"
    provider.search_sources.return_value = []
    service = WatchSourceSyncService(watch_repo, [provider])

    service.sync_for_anime(anime_id=5, anime=anime_factory(title="Mob Psycho 100"), episode=1)
    service.sync_for_anime(
        anime_id=5,
        anime=anime_factory(title="Mob Psycho 100"),
        episode=1,
        force=force_second_call,
    )

    assert provider.search_sources.call_count == expected_calls


def test_watch_source_sync_service_saves_discovered_sources(anime_factory):
    """Проверяем, что найденные источники сохраняются через репозиторий и не попадают в empty-cache."""
    watch_repo = Mock()
    watch_repo.get_sources.side_effect = [[], []]
    watch_repo.add_translation.side_effect = lambda translation: type(
        "TranslationStub",
        (),
        {"id": 77, "name": translation.name},
    )()
    provider = Mock()
    provider.is_enabled.return_value = True
    provider.provider_name = "AniLibria"
    provider.search_sources.return_value = [
        DiscoveredWatchSource(
            episode=1,
            translation_name="AniLibria",
            translation_type="voice",
            provider_name="AniLibria",
            source_name="release",
            quality_label="1080",
            stream_url="https://example.com/hls.m3u8",
        )
    ]
    service = WatchSourceSyncService(watch_repo, [provider])

    service.sync_for_anime(
        anime_id=10,
        anime=anime_factory(title="Gintama"),
        episode=1,
    )

    assert watch_repo.add_translation.call_count == 1
    assert watch_repo.add_source.call_count == 1
    assert service.empty_result_cache.contains(("anilibria", 10, 1, 2024, ("Gintama",))) is False
