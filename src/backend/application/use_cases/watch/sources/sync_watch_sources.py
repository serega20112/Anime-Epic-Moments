"""Синхронизация источников из внешних провайдеров."""

from __future__ import annotations

import asyncio

from starlette import status

from backend.application.dto import SyncWatchSourcesQuery
from backend.application.interface.services import (
    AnimeApiClientInterface,
    WatchSourceSyncServiceInterface,
)
from backend.application.interface.unit_of_work import UnitOfWorkInterface
from backend.application.use_cases.result import UseCaseResult
from backend.domain.entities.anime.anime import Anime

SYNC_TIMEOUT_SECONDS = 10


class SyncWatchSourcesUseCase:
    """Подтягивает источники просмотра из внешнего провайдера."""

    def __init__(
        self,
        unit_of_work: UnitOfWorkInterface,
        anime_api_client: AnimeApiClientInterface,
        watch_source_sync_service: WatchSourceSyncServiceInterface,
    ) -> None:
        """Инициализирует сценарий синхронизации источников просмотра.

        Args:
            unit_of_work: Граница транзакции найденных источников.
            anime_api_client: Клиент API аниме.
            watch_source_sync_service: Сервис синхронизации источников просмотра.
        """
        self._unit_of_work = unit_of_work
        self.anime_api_client = anime_api_client
        self.watch_source_sync_service = watch_source_sync_service

    async def execute(self, query: SyncWatchSourcesQuery) -> UseCaseResult:
        """Подтянуть источники просмотра для серии.

        Сценарий сам задаёт границу транзакции: найденные у провайдеров
        источники и озвучки записываются в единицу работы и фиксируются при
        успешном выходе из неё. Таймаут сетевого поиска выходит из контекста
        с ошибкой, поэтому неполная выборка откатывается, а не оседает
        незакоммиченной в сессии запроса.

        Args:
            query: Аниме, серия и признак принудительного обновления.

        Returns:
            UseCaseResult: Сводка по найденным источникам либо код ошибки.
        """
        if not await self.watch_source_sync_service.is_enabled():
            return UseCaseResult.failure(
                "provider_not_configured", status_code=status.HTTP_400_BAD_REQUEST
            )
        anime = await self.anime_api_client.get_by_id(query.anime_id)
        try:
            async with self._unit_of_work as uow:
                sources = await asyncio.wait_for(
                    self.watch_source_sync_service.sync_for_anime(
                        unit_of_work=uow,
                        anime_id=query.anime_id,
                        anime=anime,
                        episode=query.episode,
                        force=query.force,
                    ),
                    timeout=SYNC_TIMEOUT_SECONDS,
                )
        except TimeoutError:
            return UseCaseResult.failure(
                "provider_timeout", status_code=status.HTTP_504_GATEWAY_TIMEOUT
            )
        if len(sources) == 0:
            return UseCaseResult.failure("no_sources_found", status_code=status.HTTP_404_NOT_FOUND)
        if not await self._episode_available_for_any_translation(anime, query.episode):
            return UseCaseResult.failure(
                "episode_not_available_for_translation", status_code=status.HTTP_404_NOT_FOUND
            )
        return UseCaseResult.success(
            {
                "enabled": True,
                "sources_count": len(sources),
                "provider_names": await self.watch_source_sync_service.get_enabled_provider_names(),
            }
        )

    async def _episode_available_for_any_translation(
        self,
        anime: Anime | None,
        episode: int,
    ) -> bool:
        """Проверяет, доступна ли серия хотя бы у одной озвучки.

        Fail-fast: если серия отсутствует у всех озвучек (по карте
        доступности провайдера), возвращается False — вызывающий код
        отдаёт 404 вместо подмены контента похожим тайтлом.

        Args:
            anime: Сущность Anime или None.
            episode: Номер серии.

        Returns:
            bool: True, если карта доступности пуста (провайдер не поддерживает)
            или серия есть хотя бы у одной озвучки.
        """
        if anime is None or not getattr(anime, "title", None):
            return True
        availability = await self.watch_source_sync_service.get_translations_availability(
            title=anime.title,
            year=anime.year,
            shikimori_id=anime.mal_id,
            genres=anime.genres,
        )
        if not availability:
            return True
        return any(record.has_episode(episode) for record in availability)
