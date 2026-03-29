from abc import ABC, abstractmethod
from typing import List, Optional

from src.backend.domain.highlight.entity import Highlight
from src.backend.domain.highlight.value_object import (
    HighlightActivityItem,
    HighlightCommentItem,
    HighlightEngagement,
    HighlightLikeUser,
    HighlightProfileSummary,
)


class HighlightRepository(ABC):
    @abstractmethod
    def add(self, highlight: Highlight) -> Highlight:
        """Сохраняет новый хайлайт и возвращает с id"""

    @abstractmethod
    def update(self, highlight: Highlight) -> Highlight:
        """Обновляет существующий хайлайт"""

    @abstractmethod
    def delete(self, highlight_id: int):
        """Удаляет хайлайт по id"""

    @abstractmethod
    def get_by_id(self, highlight_id: int) -> Optional[Highlight]:
        """Возвращает Highlight по id"""

    @abstractmethod
    def get_by_user(self, user_id: int) -> List[Highlight]:
        """Возвращает все хайлайты пользователя"""

    @abstractmethod
    def get_by_users(self, user_ids: List[int], limit: int | None = None) -> List[Highlight]:
        """Возвращает хайлайты нескольких пользователей."""

    @abstractmethod
    def get_public_top(self, limit: int = 20) -> List[Highlight]:
        """Возвращает топ публичных хайлайтов по лайкам"""

    @abstractmethod
    def get_public_recent(self, limit: int = 20) -> List[Highlight]:
        """Возвращает новые публичные хайлайты"""

    @abstractmethod
    def get_by_anime_episode(
        self, anime_id: int, episode: int, user_id: int | None = None
    ) -> List[Highlight]:
        """Возвращает хайлайты по аниме и серии"""

    @abstractmethod
    def get_saved_by_user(self, user_id: int, limit: int | None = None) -> List[Highlight]:
        """Возвращает сохраненные пользователем хайлайты"""

    @abstractmethod
    def get_liked_by_user(self, user_id: int, limit: int | None = None) -> List[Highlight]:
        """Возвращает хайлайты, которые пользователь лайкнул"""

    @abstractmethod
    def get_from_anime_ids(
        self,
        anime_ids: List[int],
        limit: int = 20,
    ) -> List[Highlight]:
        """Возвращает хайлайты из заданного набора аниме"""

    @abstractmethod
    def set_like(self, highlight_id: int, user_id: int, liked: bool) -> Highlight:
        """Ставит или снимает лайк с хайлайта"""

    @abstractmethod
    def get_likers(self, highlight_id: int, limit: int = 20) -> List[HighlightLikeUser]:
        """Возвращает пользователей, лайкнувших хайлайт"""

    @abstractmethod
    def add_comment(
        self, highlight_id: int, user_id: int, content: str
    ) -> HighlightCommentItem:
        """Добавляет комментарий к хайлайту"""

    @abstractmethod
    def get_comments(
        self, highlight_id: int, limit: int = 20
    ) -> List[HighlightCommentItem]:
        """Возвращает комментарии хайлайта"""

    @abstractmethod
    def set_saved(self, highlight_id: int, user_id: int, saved: bool) -> bool:
        """Сохраняет или удаляет хайлайт из сохраненных"""

    @abstractmethod
    def get_engagement_map(
        self, highlight_ids: List[int], viewer_user_id: int | None = None
    ) -> dict[int, HighlightEngagement]:
        """Возвращает социальные метрики для набора хайлайтов"""

    @abstractmethod
    def increment_views(self, highlight_id: int) -> Highlight:
        """Увеличивает счетчик просмотров хайлайта"""

    @abstractmethod
    def get_profile_summary(self, user_id: int) -> HighlightProfileSummary:
        """Возвращает счетчики хайлайтов, лайков и сохранений пользователя"""

    @abstractmethod
    def get_recent_activity(
        self, user_id: int, limit: int = 10
    ) -> List[HighlightActivityItem]:
        """Возвращает последние реакции сообщества на хайлайты пользователя"""
