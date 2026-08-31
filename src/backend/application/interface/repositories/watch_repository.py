from abc import ABC, abstractmethod

from backend.domain.entities.watch.highlight_context import HighlightContext
from backend.domain.entities.watch.translation import Translation
from backend.domain.entities.watch.user_anime_status import UserAnimeStatus
from backend.domain.entities.watch.viewing_session import ViewingSession
from backend.domain.entities.watch.watch_source import WatchSource
from backend.domain.value_objects.anime.discussion import AnimeDiscussionComment
from backend.domain.value_objects.watch.page_data import ViewingHeatmapPoint, WatchedAnimeStat


class WatchRepository(ABC):
    @abstractmethod
    async def get_status(self, user_id: int, anime_id: int) -> UserAnimeStatus | None:
        """Возвращает статус просмотра пользователя."""

    @abstractmethod
    async def get_statuses_by_user(self, user_id: int) -> list[UserAnimeStatus]:
        """Возвращает записи дневника пользователя."""

    @abstractmethod
    async def upsert_status(self, status: UserAnimeStatus) -> UserAnimeStatus:
        """Создает или обновляет статус просмотра пользователя."""

    @abstractmethod
    async def record_episode_completion(
        self,
        user_id: int,
        anime_id: int,
        episode: int,
    ) -> UserAnimeStatus:
        """Advance the user's anime progress after finishing an episode."""

    @abstractmethod
    async def get_translations(self, anime_id: int) -> list[Translation]:
        """Возвращает список озвучек/сабов аниме."""

    @abstractmethod
    async def add_translation(self, translation: Translation) -> Translation:
        """Создает новую озвучку/сабы."""

    @abstractmethod
    async def get_sources(self, anime_id: int, episode: int | None = None) -> list[WatchSource]:
        """Возвращает источники просмотра."""

    @abstractmethod
    async def add_source(self, source: WatchSource) -> WatchSource:
        """Создает источник просмотра."""

    @abstractmethod
    async def get_session(self, user_id: int, anime_id: int, episode: int) -> ViewingSession | None:
        """Возвращает последнюю сессию просмотра."""

    @abstractmethod
    async def upsert_session(self, session: ViewingSession) -> ViewingSession:
        """Создает или обновляет сессию просмотра."""

    @abstractmethod
    async def add_highlight_context(self, context: HighlightContext) -> HighlightContext:
        """Сохраняет связь хайлайта с источником и озвучкой."""

    @abstractmethod
    async def get_highlight_contexts(self, highlight_ids: list[int]) -> list[HighlightContext]:
        """Возвращает контексты для набора хайлайтов."""

    @abstractmethod
    async def get_watched_anime_stats(
        self,
        user_id: int,
        limit: int | None = None,
    ) -> list[WatchedAnimeStat]:
        """Возвращает агрегированную статистику просмотра по аниме."""

    @abstractmethod
    async def get_viewing_heatmap(
        self,
        user_id: int,
        days: int = 35,
    ) -> list[ViewingHeatmapPoint]:
        """Возвращает тепловую карту активности просмотра по дням."""

    @abstractmethod
    async def add_anime_comment(
        self,
        anime_id: int,
        user_id: int,
        content: str,
    ) -> AnimeDiscussionComment:
        """Добавляет комментарий в обсуждение аниме."""

    @abstractmethod
    async def get_anime_comments(
        self,
        anime_id: int,
        sort_by: str = "popular",
        viewer_user_id: int | None = None,
        limit: int = 20,
    ) -> list[AnimeDiscussionComment]:
        """Возвращает комментарии обсуждения аниме."""

    @abstractmethod
    async def set_anime_comment_like(
        self,
        comment_id: int,
        user_id: int,
        liked: bool,
    ) -> AnimeDiscussionComment:
        """Ставит или снимает лайк с комментария в обсуждении аниме."""
