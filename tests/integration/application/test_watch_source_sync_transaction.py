from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from backend.application.dto import SyncWatchSourcesQuery
from backend.application.services.watch_source_service import WatchSourceSyncService
from backend.application.use_cases import SyncWatchSourcesUseCase
from backend.domain.entities.anime.anime import Anime
from backend.domain.value_objects.watch.discovery import DiscoveredWatchSource
from backend.infrastructure.cache.ttl_cache import TTLCache
from backend.infrastructure.database.repositories.watch_repository import WatchRepository
from backend.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork

ANIME_ID = 777


class _SingleSourceProvider:
    """Провайдер, всегда находящий один источник с прямым потоком."""

    provider_name = "Fakebox"
    ephemeral_links = False

    async def is_enabled(self) -> bool:
        """Сообщить, что провайдер включён."""
        return True

    async def search_sources(
        self,
        title: str,
        episode: int,
        year: int | None = None,
        shikimori_id: int | None = None,
    ) -> list[DiscoveredWatchSource]:
        """Вернуть один найденный источник вне зависимости от запроса."""
        return [
            DiscoveredWatchSource(
                episode=episode,
                translation_name="Fakebox",
                translation_type="voice",
                language="ru",
                provider_name=self.provider_name,
                source_name=f"fake-{title[:8]}-{episode}",
                stream_url="https://example.com/fake.mp4",
                quality_label="1080p",
                source_type="stream",
            )
        ]

    async def get_translations_availability(self, title, year=None, shikimori_id=None):
        """Не поддерживать карту доступности серий."""
        return []


@pytest.mark.integration
class TestWatchSourceSyncTransaction:
    """Интеграционная проверка границы транзакции синхронизации источников."""

    async def test_synced_sources_survive_request_session_close(
        self, async_db_session_factory
    ) -> None:
        """Что тестируем: сохранение найденных источников после окончания запроса.
        Что передаём: реальные WatchRepository, SqlAlchemyUnitOfWork и сервис с
        фейковым провайдером; сессия запроса закрывается сразу после сценария.
        Что ожидаем: источник и озвучка видны в новой сессии. До переноса записи
        в единицу работы сценария они молча откатывались, а эндпоинт отвечал 200.
        """
        service = WatchSourceSyncService(
            [_SingleSourceProvider()],
            empty_result_cache=TTLCache(ttl_seconds=600, max_entries=32),
            availability_cache=TTLCache(ttl_seconds=1800, max_entries=32),
        )
        anime_api_client = AsyncMock()
        anime_api_client.get_by_id.return_value = Anime(
            external_id="12345", title="Gintama", year=2011, genres=["Action"]
        )
        async with async_db_session_factory() as session:
            use_case = SyncWatchSourcesUseCase(
                SqlAlchemyUnitOfWork(session),
                anime_api_client,
                service,
            )

            result = await use_case.execute(SyncWatchSourcesQuery(anime_id=ANIME_ID, episode=1))

        assert result.ok is True
        assert result.data["sources_count"] == 1

        async with async_db_session_factory() as next_session:
            stored = await WatchRepository(next_session).get_sources(anime_id=ANIME_ID, episode=1)
            translations = await WatchRepository(next_session).get_translations(ANIME_ID)

        assert [item.stream_url for item in stored] == ["https://example.com/fake.mp4"]
        assert [item.name for item in translations] == ["Fakebox"]
