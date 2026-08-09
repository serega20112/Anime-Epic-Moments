from abc import ABC, abstractmethod

from backend.domain.highlight.entity import Highlight
from backend.domain.highlight.value_object import (
    HighlightActivityItem,
    HighlightCommentItem,
    HighlightEngagement,
    HighlightLikeUser,
    HighlightProfileSummary,
)


class HighlightRepository(ABC):
    @abstractmethod
    async def add(self, highlight: Highlight) -> Highlight:
        """Сохраняет новый хайлайт и возвращает с id"""

    @abstractmethod
    async def update(self, highlight: Highlight) -> Highlight:
        """Обновляет существующий хайлайт"""

    @abstractmethod
    async def delete(self, highlight_id: int):
        """Удаляет хайлайт по id"""

    @abstractmethod
    async def get_by_id(self, highlight_id: int) -> Highlight | None:
        """Возвращает Highlight по id"""

    @abstractmethod
    async def get_by_user(self, user_id: int) -> list[Highlight]:
        """Возвращает все хайлайты пользователя"""

    @abstractmethod
    async def get_by_users(self, user_ids: list[int], limit: int | None = None) -> list[Highlight]:
        """Возвращает хайлайты нескольких пользователей."""

    @abstractmethod
    async def get_public_top(self, limit: int = 20) -> list[Highlight]:
        """Возвращает топ публичных хайлайтов по лайкам"""

    @abstractmethod
    async def get_public_recent(self, limit: int = 20) -> list[Highlight]:
        """Возвращает новые публичные хайлайты"""

    @abstractmethod
    async def get_by_anime_episode(
            self, anime_id: int, episode: int, user_id: int | None = None
    ) -> list[Highlight]:
        """Возвращает хайлайты по аниме и серии"""

    @abstractmethod
    async def get_saved_by_user(self, user_id: int, limit: int | None = None) -> list[Highlight]:
        """Возвращает сохраненные пользователем хайлайты"""

    @abstractmethod
    async def get_liked_by_user(self, user_id: int, limit: int | None = None) -> list[Highlight]:
        """Возвращает хайлайты, которые пользователь лайкнул"""

    @abstractmethod
    async def get_from_anime_ids(
            self,
            anime_ids: list[int],
            limit: int = 20,
    ) -> list[Highlight]:
        """Возвращает хайлайты из заданного набора аниме"""

    @abstractmethod
    async def set_like(self, highlight_id: int, user_id: int, liked: bool) -> Highlight:
        """Ставит или снимает лайк с хайлайта"""

    @abstractmethod
    async def get_likers(self, highlight_id: int, limit: int = 20) -> list[HighlightLikeUser]:
        """Возвращает пользователей, лайкнувших хайлайт"""

    @abstractmethod
    async def add_comment(
            self, highlight_id: int, user_id: int, content: str
    ) -> HighlightCommentItem:
        """Добавляет комментарий к хайлайту"""

    @abstractmethod
    async def get_comments(self, highlight_id: int, limit: int = 20) -> list[HighlightCommentItem]:
        """Возвращает комментарии хайлайта"""

    @abstractmethod
    async def set_saved(self, highlight_id: int, user_id: int, saved: bool) -> bool:
        """Сохраняет или удаляет хайлайт из сохраненных"""

    @abstractmethod
    async def get_engagement_map(
            self, highlight_ids: list[int], viewer_user_id: int | None = None
    ) -> dict[int, HighlightEngagement]:
        """Возвращает социальные метрики для набора хайлайтов"""

    @abstractmethod
    async def increment_views(self, highlight_id: int) -> Highlight:
        """Увеличивает счетчик просмотров хайлайта"""

    @abstractmethod
    async def get_profile_summary(self, user_id: int) -> HighlightProfileSummary:
        """Возвращает счетчики хайлайтов, лайков и сохранений пользователя"""

    @abstractmethod
    async def get_recent_activity(
            self, user_id: int, limit: int = 10
    ) -> list[HighlightActivityItem]:
        """Возвращает последние реакции сообщества на хайлайты пользователя"""
