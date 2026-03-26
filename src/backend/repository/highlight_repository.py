from abc import ABC, abstractmethod
from typing import List, Optional
from src.backend.domain.highlight.entity import Highlight


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
    def get_public_top(self, limit: int = 20) -> List[Highlight]:
        """Возвращает топ публичных хайлайтов по лайкам"""

    @abstractmethod
    def get_by_anime_episode(self, anime_id: int, episode: int, user_id: int | None = None) -> List[Highlight]:
        """Возвращает хайлайты по аниме и серии"""
