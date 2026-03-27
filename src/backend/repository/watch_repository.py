from abc import ABC, abstractmethod
from typing import List, Optional
from src.backend.domain.watch.entity import (
    HighlightContext,
    Translation,
    UserAnimeStatus,
    ViewingSession,
    WatchSource,
)


class WatchRepository(ABC):
    @abstractmethod
    def get_status(self, user_id: int, anime_id: int) -> Optional[UserAnimeStatus]:
        """Возвращает статус просмотра пользователя."""

    @abstractmethod
    def upsert_status(self, status: UserAnimeStatus) -> UserAnimeStatus:
        """Создает или обновляет статус просмотра пользователя."""

    @abstractmethod
    def get_translations(self, anime_id: int) -> List[Translation]:
        """Возвращает список озвучек/сабов аниме."""

    @abstractmethod
    def add_translation(self, translation: Translation) -> Translation:
        """Создает новую озвучку/сабы."""

    @abstractmethod
    def get_sources(
        self, anime_id: int, episode: int | None = None
    ) -> List[WatchSource]:
        """Возвращает источники просмотра."""

    @abstractmethod
    def add_source(self, source: WatchSource) -> WatchSource:
        """Создает источник просмотра."""

    @abstractmethod
    def get_session(
        self, user_id: int, anime_id: int, episode: int
    ) -> Optional[ViewingSession]:
        """Возвращает последнюю сессию просмотра."""

    @abstractmethod
    def upsert_session(self, session: ViewingSession) -> ViewingSession:
        """Создает или обновляет сессию просмотра."""

    @abstractmethod
    def add_highlight_context(self, context: HighlightContext) -> HighlightContext:
        """Сохраняет связь хайлайта с источником и озвучкой."""

    @abstractmethod
    def get_highlight_contexts(
        self, highlight_ids: List[int]
    ) -> List[HighlightContext]:
        """Возвращает контексты для набора хайлайтов."""
