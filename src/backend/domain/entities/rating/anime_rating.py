from __future__ import annotations

from datetime import datetime


class UserAnimeRating:
    """Оценка пользователя по конкретному аниме.

    Оценка выставляется по шкале от 1 до 5, одна запись на пару
    (пользователь, аниме). Дубликаты исключаются на уровне хранилища.
    """

    SCORE_MIN = 1
    SCORE_MAX = 5

    def __init__(
        self,
        user_id: int,
        anime_id: int,
        score: int,
        rated_at: datetime | None = None,
    ):
        """Создать оценку.

        Args:
            user_id: Идентификатор пользователя-автора.
            anime_id: Идентификатор аниме.
            score: Оценка от 1 до 5.
            rated_at: Время выставления оценки.

        Raises:
            ValueError: Когда оценка вне допустимого диапазона.
        """
        if not (self.SCORE_MIN <= int(score) <= self.SCORE_MAX):
            raise ValueError(
                f"Оценка должна быть от {self.SCORE_MIN} до {self.SCORE_MAX}, сейчас {score}"
            )
        self.user_id = int(user_id)
        self.anime_id = int(anime_id)
        self.score = int(score)
        self.rated_at = rated_at or datetime.utcnow()

    def update_score(self, score: int):
        """Перевыставить оценку с проверкой диапазона.

        Args:
            score: Новая оценка от 1 до 5.
        """
        if not (self.SCORE_MIN <= int(score) <= self.SCORE_MAX):
            raise ValueError(
                f"Оценка должна быть от {self.SCORE_MIN} до {self.SCORE_MAX}, сейчас {score}"
            )
        self.score = int(score)
