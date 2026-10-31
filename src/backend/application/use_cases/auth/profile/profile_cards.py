"""Карточки профиля, собираемые из данных базы и карточек каталога.

Правила отображения вынесены из сценария: они не ходят в сеть и не трогают
транзакцию, поэтому проверяются напрямую на списках сущностей.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from statistics import mean

from backend.domain import (
    Favorite,
    RecentEpisodeCard,
    TopAnimeEntry,
    UserAnimeRating,
    UserRatingCard,
    ViewingSession,
)
from backend.domain.entities.anime.anime import Anime

AnimeCard = Anime | None

ANIME_ID_FALLBACK_TEMPLATE = "Anime #{anime_id}"


def collect_genres(
    favorites: Iterable[Favorite],
    anime_map: dict[int, AnimeCard],
) -> list[str]:
    """Собрать плоский список жанров избранного и карточек тайтлов.

    Args:
        favorites: Избранные тайтлы пользователя.
        anime_map: Карточки тайтлов по идентификатору.

    Returns:
        list[str]: Жанры с повторами — частоту считает доменная политика.
    """
    genres: list[str] = []
    for favorite in favorites:
        if favorite.genres:
            genres.extend(favorite.genres)
            continue
        anime = anime_map.get(int(favorite.anime_id))
        if anime and anime.genres:
            genres.extend(anime.genres)
    for anime in anime_map.values():
        if anime and anime.genres:
            genres.extend(anime.genres)
    return genres


def build_top_anime(
    ranked_weights: Sequence[tuple[int, float]],
    anime_map: dict[int, AnimeCard],
) -> list[TopAnimeEntry]:
    """Собрать карточки самых заметных тайтлов по весу внимания.

    Args:
        ranked_weights: Пары «идентификатор, вес» в порядке убывания веса.
        anime_map: Карточки тайтлов по идентификатору.

    Returns:
        list[TopAnimeEntry]: Карточки заметных тайтлов.
    """
    cards: list[TopAnimeEntry] = []
    for anime_id, weight in ranked_weights:
        anime = anime_map.get(anime_id)
        cards.append(
            TopAnimeEntry(
                anime_id=anime_id,
                title=title_of(anime, anime_id),
                cover_url=anime.cover_url if anime else None,
                rating=anime.rating if anime else None,
                weight=round(float(weight), 1),
            )
        )
    return cards


def build_rating_cards(
    ratings: Iterable[UserAnimeRating],
    anime_map: dict[int, AnimeCard],
) -> list[UserRatingCard]:
    """Собрать карточки оценок пользователя с названиями тайтлов.

    Args:
        ratings: Оценки пользователя по тайтлам.
        anime_map: Карточки тайтлов по идентификатору.

    Returns:
        list[UserRatingCard]: Карточки оценок для отображения.
    """
    return [
        UserRatingCard(
            anime_id=int(item.anime_id),
            title=title_of(anime_map.get(int(item.anime_id)), int(item.anime_id)),
            cover_url=cover_of(anime_map.get(int(item.anime_id))),
            score=item.score,
            rated_at=item.rated_at.strftime("%Y-%m-%d %H:%M"),
        )
        for item in ratings
    ]


def build_recent_episode_cards(
    sessions: Iterable[ViewingSession],
    anime_map: dict[int, AnimeCard],
) -> list[RecentEpisodeCard]:
    """Собрать карточки недавно просмотренных серий.

    Args:
        sessions: Последние сессии просмотра.
        anime_map: Карточки тайтлов по идентификатору.

    Returns:
        list[RecentEpisodeCard]: Карточки серий для панели активности.
    """
    return [
        RecentEpisodeCard(
            anime_id=int(item.anime_id),
            title=title_of(anime_map.get(int(item.anime_id)), int(item.anime_id)),
            original_title=original_title_of(anime_map.get(int(item.anime_id))),
            cover_url=cover_of(anime_map.get(int(item.anime_id))),
            episode=int(item.episode),
            updated_at=item.updated_at,
        )
        for item in sessions
    ]


def average_catalog_rating(anime_map: dict[int, AnimeCard]) -> float | None:
    """Посчитать среднюю оценку каталога по тайтлам пользователя.

    Args:
        anime_map: Карточки тайтлов по идентификатору.

    Returns:
        float | None: Средняя оценка либо None, если оценок нет.
    """
    rating_values = [
        float(anime.rating) for anime in anime_map.values() if anime and anime.rating is not None
    ]
    return round(mean(rating_values), 1) if rating_values else None


def title_of(anime: AnimeCard, anime_id: int) -> str:
    """Вернуть название аниме или подпись по его идентификатору.

    Args:
        anime: Карточка тайтла из каталога либо None.
        anime_id: Идентификатор тайтла.

    Returns:
        str: Название тайтла либо запасная подпись.
    """
    title = str(anime.title or "").strip() if anime else ""
    return title or ANIME_ID_FALLBACK_TEMPLATE.format(anime_id=anime_id)


def cover_of(anime: AnimeCard) -> str | None:
    """Вернуть обложку тайтла, если карточка каталога получена.

    Args:
        anime: Карточка тайтла из каталога либо None.

    Returns:
        str | None: Ссылка на обложку либо None.
    """
    return anime.cover_url if anime else None


def original_title_of(anime: AnimeCard) -> str | None:
    """Вернуть оригинальное название тайтла, если оно доступно.

    Args:
        anime: Карточка тайтла из каталога либо None.

    Returns:
        str | None: Оригинальное название либо None.
    """
    return anime.original_title if anime else None
