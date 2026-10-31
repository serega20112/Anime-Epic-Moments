"""Контракт провайдера внешних источников просмотра.

Провайдеры внешних источников просмотра (Kodik, AniLibria, YouTube и т.д.)
реализуют именно этот контракт. Порт лежит в прикладном слое, потому что на него
опирается сервис синхронизации источников
(:class:`backend.application.services.watch_source_service.WatchSourceSyncService`),
а инфраструктурные клиенты — лишь его реализации.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from backend.domain.value_objects.watch.discovery import DiscoveredWatchSource


class WatchSourceProviderInterface(ABC):
    """Контракт провайдера внешних источников просмотра.

    Атрибут ``ephemeral_links`` означает, что ссылка на поток живёт
    ограниченное время и не должна храниться в базе как долговременная.
    Провайдеры с подписанными URL выставляют его в True: Eporner отдаёт
    CDN-ссылку с Unix-временем в пути (TTL около двух часов), и по истечении
    срока сервер отвечает по старой ссылке минутным трейлером-заглушкой вместо
    серии. Такие источники нужно перезапрашивать на каждой синхронизации.
    """

    provider_name: str

    ephemeral_links: bool = False

    @abstractmethod
    async def is_enabled(self) -> bool:
        """Возвращает доступность провайдера."""

    @abstractmethod
    async def search_sources(
        self,
        title: str,
        episode: int,
        year: int | None = None,
        limit: int = 8,
        shikimori_id: int | None = None,
    ) -> list[DiscoveredWatchSource]:
        """Ищет источники для конкретного аниме и эпизода.

        Args:
            title: Название тайтла (используется, только когда внешний id
                недоступен).
            episode: Номер серии.
            year: Год выпуска для смягчённой сверки.
            limit: Максимум источников в результате.
            shikimori_id: Внешний id тайтла (MAL/Shikimori). Когда он задан,
                провайдеры с каталогом переводов обязаны адресоваться строго
                по нему и не прибегать к нечёткому сопоставлению названий —
                это исключает подмену контента франшизы.
        """

    async def get_translations_availability(
        self,
        title: str,
        year: int | None = None,
        shikimori_id: int | None = None,
    ) -> list:
        """Возвращает карту доступности серий по озвучкам (если провайдер умеет).

        По умолчанию провайдер не поддерживает карту доступности — возвращает
        пустой список. Строгую изоляцию серий по озвучкам реализуют провайдеры
        с каталогом переводов (Kodik).

        Args:
            title: Название тайтла.
            year: Год выпуска для смягчённой сверки.
            shikimori_id: Внешний id тайтла (MAL/Shikimori) для строгой
                адресации без текстового поиска.

        Returns:
            list[TranslationEpisodeAvailability]: Карта доступности серий
            по озвучкам (пустая, если провайдер не поддерживает).
        """
        return []
