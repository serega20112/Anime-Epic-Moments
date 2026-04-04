from abc import ABC, abstractmethod

from src.backend.domain.watch.value_object import DiscoveredWatchSource


class WatchSourceProvider(ABC):
    """Контракт провайдера внешних источников просмотра."""

    provider_name: str

    @abstractmethod
    def is_enabled(self) -> bool:
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
