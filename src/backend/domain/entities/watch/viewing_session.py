"""Сущность сессии просмотра."""

from datetime import datetime

from backend.domain.clock import utc_now

MIN_VOLUME = 0.0
MAX_VOLUME = 1.0
MIN_EPISODE = 1


class ViewingSession:
    """Позиция просмотра пользователя в конкретной серии.

    Числовые поля приходят из плеера, то есть из недоверенного ввода: позиция
    не может быть отрицательной, громкость лежит в отрезке от нуля до единицы,
    а серии начинаются с первой. Правила применяются в конструкторе, чтобы
    испорченное значение не доехало ни до базы, ни до следующего чтения.
    """

    def __init__(
        self,
        user_id: int,
        anime_id: int,
        episode: int,
        watch_source_id: int,
        position_seconds: float,
        volume: float,
        quality_label: str,
        is_paused: bool,
        id: int | None = None,
        updated_at: datetime | None = None,
    ):
        """Создать сессию просмотра, приведя поля к допустимым значениям.

        Args:
            user_id: Идентификатор зрителя.
            anime_id: Идентификатор тайтла.
            episode: Номер серии; значения меньше первой поднимаются до первой.
            watch_source_id: Идентификатор выбранного источника.
            position_seconds: Позиция воспроизведения; отрицательная сбрасывается в ноль.
            volume: Громкость плеера в границах от нуля до единицы.
            quality_label: Метка выбранного качества.
            is_paused: Признан ли плеер остановленным.
            id: Идентификатор записи в хранилище.
            updated_at: Момент последнего обновления прогресса.
        """
        self.id = id
        self.user_id = user_id
        self.anime_id = anime_id
        self.episode = max(MIN_EPISODE, int(episode))
        self.watch_source_id = watch_source_id
        self.position_seconds = max(0.0, float(position_seconds))
        self.volume = min(max(float(volume), MIN_VOLUME), MAX_VOLUME)
        self.quality_label = quality_label
        self.is_paused = bool(is_paused)
        self.updated_at = updated_at or utc_now()
