"""Abstract watch source sync service interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class WatchSourceSyncServiceInterface(ABC):
    """Interface for syncing watch sources."""

    @abstractmethod
    async def sync_sources(self, anime_id: int) -> list[Any]:
        """Sync watch sources for an anime.

        Args:
            anime_id: The anime identifier.

        Returns:
            list[Any]: List of watch source objects.
        """

    @abstractmethod
    async def add_watch_source(self, source_data: dict[str, Any]) -> Any:
        """Add a watch source.

        Args:
            source_data: Dictionary with source information.

        Returns:
            Any: The created watch source.
        """

    @abstractmethod
    async def get_translations_availability(
        self,
        title: str,
        year: int | None = None,
        shikimori_id: int | None = None,
        genres: list[str] | None = None,
    ) -> list[Any]:
        """Возвращает карту доступности серий по озвучкам тайтла.

        Args:
            title: Название тайтла.
            year: Год выпуска для смягчённой сверки.
            shikimori_id: Внешний id тайтла (MAL/Shikimori) для строгой адресации.
            genres: Жанры тайтла (для hentai контента опрашиваются только
                профильные провайдеры).

        Returns:
            list[Any]: Карта доступности серий по озвучкам; пустой список,
            если ни один провайдер не умеет.
        """
