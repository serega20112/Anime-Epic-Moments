from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from backend.application.services.watch_source_sync_service import WatchSourceSyncService
from backend.infrastructure.external.errors import ExternalServiceUnavailableError


@pytest.mark.unit
class TestWatchSourceSyncService:
    """Юнит-тесты сервиса синхронизации источников для просмотра."""

    def _service(self, providers, get_sources=None):
        watch_repo = AsyncMock()
        watch_repo.get_sources.return_value = get_sources if get_sources is not None else []
        service = WatchSourceSyncService(watch_repo, providers)
        service.empty_result_cache.clear()
        return service, watch_repo

    async def test_skips_disabled_providers(self):
        """Что тестируем: отключенные провайдеры не запрашиваются.
        Что передаём: один провайдер с is_enabled=False.
        Что ожидаем: search_sources не вызывается, возвращается только существующее.
        """
        provider = Mock()
        provider.is_enabled.return_value = False
        provider.search_sources = AsyncMock()
        service, _watch_repo = self._service([provider])

        result = await service.sync_for_anime(
            anime_id=10, anime=SimpleNamespace(title="Gintama", year=2024), episode=1
        )

        assert result == []
        provider.search_sources.assert_not_awaited()

    @pytest.mark.parametrize("force", [False, True])
    async def test_empty_result_is_cached(self, force):
        """Что тестируем: пустой результат кэшируется и повторно не пересчитывается.
        Что передаём: два вызова sync_for_anime с включенным провайдером без источников.
        Что ожидаем: при force второе обращение сбрасывает кэш, иначе кэш отсекает запрос.
        """
        provider = Mock()
        provider.provider_name = "AniLibria"
        provider.is_enabled.return_value = True
        provider.search_sources = AsyncMock(return_value=[])
        service, _watch_repo = self._service([provider])

        await service.sync_for_anime(
            anime_id=10, anime=SimpleNamespace(title="Mob Psycho 100", year=2024), episode=1
        )
        await service.sync_for_anime(
            anime_id=10,
            anime=SimpleNamespace(title="Mob Psycho 100", year=2024),
            episode=1,
            force=force,
        )

        assert (
            provider.search_sources.await_count == 2
            if force
            else provider.search_sources.await_count == 1
        )

    async def test_existing_provider_is_not_requeried(self):
        """Что тестируем: провайдер, уже записанный в репозиторий, не запрашивается повторно.
        Что передаём: существующие источники с тем же именем провайдера.
        Что ожидаем: поиск не вызывается, возвращается существующий список.
        """
        provider = Mock()
        provider.provider_name = "AniLibria"
        provider.is_enabled.return_value = True
        provider.search_sources = AsyncMock()
        existing = [SimpleNamespace(provider_name="anilibria")]
        service, _watch_repo = self._service([provider], get_sources=existing)

        result = await service.sync_for_anime(
            anime_id=10, anime=SimpleNamespace(title="Gintama", year=2024), episode=1
        )

        assert result == existing
        provider.search_sources.assert_not_awaited()

    async def test_discovered_source_saved_once(self):
        """Что тестируем: новый источник сохраняется в репозиторий без дубликатов.
        Что передаём: провайдер, возвращающий один источник по одному варианту названия.
        Что ожидаем: перевод и источник добавляются по одному разу.
        """
        provider = Mock()
        provider.provider_name = "AniLibria"
        provider.is_enabled.return_value = True
        provider.search_sources = AsyncMock(
            return_value=[
                SimpleNamespace(
                    translation_name="Gintama",
                    translation_type="subs",
                    language="russian",
                    translation_id=0,
                    episode=1,
                    provider_name="AniLibria",
                    source_name="file.mp4",
                    stream_url="https://example.com/v.mp4",
                    quality_label="1080p",
                    source_type="download",
                )
            ]
        )
        service, watch_repo = self._service([provider])
        watch_repo.add_translation.side_effect = lambda _t: SimpleNamespace(id=5)

        await service.sync_for_anime(
            anime_id=10, anime=SimpleNamespace(title="Gintama", year=2024), episode=1
        )

        provider.search_sources.assert_awaited_once()
        watch_repo.add_translation.assert_awaited_once()
        watch_repo.add_source.assert_awaited_once()

    async def test_provider_error_is_isolated(self):
        """Что тестируем: сбой одного провайдера не ломает синхронизацию остальных.
        Что передаём: первый провайдер бросает ExternalServiceUnavailableError, второй возвращает источник.
        Что ожидаем: результат включает источник второго провайдера, синхронизация не падает.
        """
        failing = Mock()
        failing.provider_name = "SameBand"
        failing.is_enabled.return_value = True
        failing.search_sources = AsyncMock(side_effect=ExternalServiceUnavailableError())

        healthy = Mock()
        healthy.provider_name = "AniLibria"
        healthy.is_enabled.return_value = True
        healthy.search_sources = AsyncMock(
            return_value=[
                SimpleNamespace(
                    translation_name="Gintama",
                    translation_type="voice",
                    language="ru",
                    translation_id=0,
                    episode=1,
                    provider_name="AniLibria",
                    source_name="file.mp4",
                    stream_url="https://example.com/v.mp4",
                    quality_label="1080p",
                    source_type="stream",
                )
            ]
        )
        service, watch_repo = self._service([failing, healthy])
        watch_repo.add_translation.side_effect = lambda _t: SimpleNamespace(id=5)

        await service.sync_for_anime(
            anime_id=10, anime=SimpleNamespace(title="Gintama", year=2024), episode=1
        )

        failing.search_sources.assert_awaited()
        healthy.search_sources.assert_awaited_once()
        watch_repo.add_source.assert_awaited_once()
