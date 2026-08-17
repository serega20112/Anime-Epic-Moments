"""Abstract watch source provider interface.

Провайдеры внешних источников просмотра (Kodik, AniLibria, YouTube и т.д.)
реализуют именно этот контракт. Интерфейс лежит в domain, потому что на него
опирается application-сервис синхронизации источников
(:class:`backend.application.services.watch_source_service.WatchSourceSyncService`),
а инфраструктурные клиенты — лишь его реализации.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from backend.domain.watch.value_object import DiscoveredWatchSource


class WatchSourceProviderInterface(ABC):
    """Контракт провайдера внешних источников просмотра."""

    provider_name: str

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
    ) -> list[DiscoveredWatchSource]:
        """Ищет источники для конкретного аниме и эпизода."""
