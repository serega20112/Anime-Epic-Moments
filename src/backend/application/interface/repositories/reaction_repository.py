from abc import ABC, abstractmethod

from backend.domain.entities.reaction.episode_reaction import EpisodeReaction
from backend.domain.value_objects.reaction.reaction_summary import EpisodeReactionCount


class ReactionRepository(ABC):
    @abstractmethod
    async def set_reaction(self, reaction: EpisodeReaction) -> EpisodeReaction:
        """Создает или обновляет реакцию пользователя на эпизод."""

    @abstractmethod
    async def remove_reaction(self, user_id: int, anime_id: int, episode: int) -> bool:
        """Удаляет реакцию пользователя на эпизод."""

    @abstractmethod
    async def get_reaction_counts(
        self,
        anime_id: int,
        episode: int,
    ) -> list[EpisodeReactionCount]:
        """Возвращает количество реакций каждого типа для эпизода."""

    @abstractmethod
    async def get_user_reaction(
        self,
        user_id: int,
        anime_id: int,
        episode: int,
    ) -> EpisodeReaction | None:
        """Возвращает текущую реакцию пользователя на эпизод."""
