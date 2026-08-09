from __future__ import annotations

from unittest.mock import Mock

from backend.application.use_cases import SyncWatchSourcesUseCase


def test_sync_watch_sources_returns_disabled_result_when_service_is_off(anime_factory):
    """Проверяем, что SyncWatchSourcesUseCase возвращает disabled payload, если discovery выключен."""
    anime_api_client = Mock()
    anime_api_client.get_by_id.return_value = anime_factory(title="Gintama")
    sync_service = Mock()
    sync_service.is_enabled.return_value = False
    use_case = SyncWatchSourcesUseCase(anime_api_client, sync_service)

    result = use_case.execute(anime_id=7, episode=2)

    assert result == {"enabled": False, "sources_count": 0, "provider_names": []}


def test_sync_watch_sources_returns_provider_names_when_enabled(anime_factory):
    """Проверяем, что SyncWatchSourcesUseCase возвращает количество найденных источников и имена провайдеров."""
    anime_api_client = Mock()
    anime_api_client.get_by_id.return_value = anime_factory(title="Gintama")
    sync_service = Mock()
    sync_service.is_enabled.return_value = True
    sync_service.sync_for_anime.return_value = ["s1", "s2"]
    sync_service.get_enabled_provider_names.return_value = ["Kodik", "AniLibria"]
    use_case = SyncWatchSourcesUseCase(anime_api_client, sync_service)

    result = use_case.execute(anime_id=7, episode=2, force=True)

    assert result == {
        "enabled": True,
        "sources_count": 2,
        "provider_names": ["Kodik", "AniLibria"],
    }
    sync_service.sync_for_anime.assert_called_once()
