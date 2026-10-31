"""Порт сервиса синхронизации источников просмотра."""

from __future__ import annotations

from abc import ABC, abstractmethod

from backend.application.interface.unit_of_work import UnitOfWorkInterface
from backend.domain.entities.anime.anime import Anime
from backend.domain.entities.watch.watch_source import WatchSource
from backend.domain.value_objects.watch.translation_availability import (
    TranslationEpisodeAvailability,
)


class WatchSourceSyncServiceInterface(ABC):
    """Синхронизация источников и доступности озвучек.

    Границу транзакции задаёт вызывающий сценарий: запись источников всегда
    выполняется через переданную единицу работы, поэтому сервис не держит
    собственный репозиторий и не решает, когда фиксировать изменения.
    """

    @abstractmethod
    async def sync_for_anime(
        self,
        unit_of_work: UnitOfWorkInterface,
        anime_id: int,
        anime: Anime | None,
        episode: int,
        force: bool = False,
    ) -> list[WatchSource]:
        """Подтянуть и сохранить источники для конкретной серии тайтла.

        Args:
            unit_of_work: Граница транзакции вызывающего сценария.
            anime_id: Идентификатор тайтла в локальном каталоге.
            anime: Карточка тайтла из каталога либо None.
            episode: Номер серии.
            force: Признак принудительного опроса, сбрасывающего кэш отметок.

        Returns:
            list[WatchSource]: Источники серии после синхронизации.
        """

    @abstractmethod
    async def is_enabled(self) -> bool:
        """Проверить, включён ли хотя бы один внешний провайдер.

        Returns:
            bool: True, если есть хотя бы один включённый провайдер.
        """

    @abstractmethod
    async def get_enabled_provider_names(self) -> list[str]:
        """Перечислить имена включённых провайдеров.

        Returns:
            list[str]: Имена включённых провайдеров.
        """

    @abstractmethod
    async def get_provider_label(self) -> str | None:
        """Собрать подпись провайдеров для интерфейса.

        Returns:
            str | None: Перечисленные через запятую имена либо None, если
            включённых провайдеров нет.
        """

    @abstractmethod
    async def get_translations_availability(
        self,
        title: str,
        year: int | None = None,
        shikimori_id: int | None = None,
        genres: list[str] | None = None,
    ) -> list[TranslationEpisodeAvailability]:
        """Вернуть карту доступности серий по озвучкам тайтла.

        Args:
            title: Название тайтла.
            year: Год выпуска для смягчённой сверки.
            shikimori_id: Внешний id тайтла (MAL/Shikimori) для строгой адресации.
            genres: Жанры тайтла (для hentai контента опрашиваются только
                профильные провайдеры).

        Returns:
            list[TranslationEpisodeAvailability]: Карта доступности серий по
            озвучкам; пустой список, если ни один провайдер её не поддерживает.
        """
