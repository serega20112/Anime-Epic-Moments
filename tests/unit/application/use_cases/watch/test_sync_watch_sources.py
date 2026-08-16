from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from backend.application.use_cases import SyncWatchSourcesUseCase


@pytest.mark.unit
class TestSyncWatchSourcesUseCase:
    """Юнит-тесты подтягивания источников просмотра."""

    async def test_returns_disabled_result_when_service_is_off(self, anime_factory):
        """Что тестируем: disabled-результат при выключенном discovery.
        Что передаём: выключенный sync_service.
        Что ожидаем: результат failure со статусом 400, sync_for_anime не вызывается.
        """
        anime_api_client = AsyncMock()
        anime_api_client.get_by_id.return_value = anime_factory(title="Gintama")
        sync_service = AsyncMock()
        sync_service.is_enabled.return_value = False
        use_case = SyncWatchSourcesUseCase(anime_api_client, sync_service, AsyncMock())

        result = await use_case.execute(anime_id=7, episode=2)

        assert result.ok is False
        assert result.status_code == 400
        sync_service.sync_for_anime.assert_not_awaited()

    async def test_returns_provider_names_when_enabled(self, anime_factory):
        """Что тестируем: количество найденных источников и имена провайдеров.
        Что передаём: включенный sync_service с двумя источниками.
        Что ожидаем: результат success с payload enabled/sources_count/provider_names.
        """
        anime_api_client = AsyncMock()
        anime_api_client.get_by_id.return_value = anime_factory(title="Gintama")
        sync_service = AsyncMock()
        sync_service.is_enabled.return_value = True
        sync_service.sync_for_anime.return_value = ["s1", "s2"]
        sync_service.get_enabled_provider_names.return_value = ["Kodik", "AniLibria"]
        use_case = SyncWatchSourcesUseCase(anime_api_client, sync_service, AsyncMock())

        result = await use_case.execute(anime_id=7, episode=2, force=True)

        assert result.ok is True
        assert result.data == {
            "enabled": True,
            "sources_count": 2,
            "provider_names": ["Kodik", "AniLibria"],
        }
        sync_service.sync_for_anime.assert_awaited_once()
