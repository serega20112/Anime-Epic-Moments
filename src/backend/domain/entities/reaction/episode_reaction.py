"""Сущность реакции на эпизод."""

from datetime import datetime

from backend.domain.clock import utc_now
from backend.domain.value_objects.reaction.reaction_type import EpisodeReactionType


class EpisodeReaction:
    """Реакция пользователя на момент внутри серии.

    Момент ставится по метке плеера, поэтому отрицательная метка не имеет
    смысла и приводится к нулю: иначе сортировка реакции по таймлайне
    отдавала бы событие «до начала серии».
    """

    def __init__(
        self,
        user_id: int,
        anime_id: int,
        episode: int,
        reaction_type: EpisodeReactionType,
        timestamp: float = 0.0,
        id: int | None = None,
        created_at: datetime | None = None,
    ):
        """Создать реакцию, приведя метку таймлайна к допустимой.

        Args:
            user_id: Идентификатор пользователя.
            anime_id: Идентификатор тайтла.
            episode: Номер серии.
            reaction_type: Тип реакции.
            timestamp: Позиция в секундах; отрицательная сбрасывается в ноль.
            id: Идентификатор записи в хранилище.
            created_at: Момент появления реакции.
        """
        self.id = id
        self.user_id = user_id
        self.anime_id = anime_id
        self.episode = episode
        self.reaction_type = reaction_type
        self.timestamp = max(0.0, float(timestamp))
        self.created_at = created_at or utc_now()
