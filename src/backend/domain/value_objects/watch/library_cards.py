"""Карточки библиотеки и истории просмотра для мобильного клиента.

Проекция читается в прикладном слое: статус дневника и сессия просмотра
дополняются карточкой каталога, а presentation лишь превращает их в JSON. Номера
серий и позиции берутся из локальных записей, заголовок и обложка — из каталога.
"""

from dataclasses import dataclass

from backend.domain.entities.anime.anime import Anime


@dataclass(frozen=True)
class LibraryAnimeCard:
    """Тайтл из дневника пользователя с его статусом и прогрессом.

    Attributes:
        anime: Карточка тайтла из каталога либо запасная заглушка.
        status: Статус просмотра в дневнике.
        current_episode: Текущая серия прогресса либо None.
        rating: Оценка пользователя либо None.
        last_watched_at: Дата последнего просмотра в текстовом виде либо None.
    """

    anime: Anime
    status: str
    current_episode: int | None
    rating: float | None
    last_watched_at: str | None


@dataclass(frozen=True)
class HistoryAnimeCard:
    """Тайтл из истории просмотров с позицией продолжения.

    Attributes:
        anime: Карточка тайтла из каталога либо запасная заглушка.
        episode: Номер серии последней сессии.
        position_seconds: Сохранённая позиция в серии.
        watched_at: Дата сессии в текстовом виде.
    """

    anime: Anime
    episode: int
    position_seconds: float
    watched_at: str
