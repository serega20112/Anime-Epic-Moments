"""Чистые функции отображения ответов провайдеров в сущность ``Anime``.

Модуль не выполняет ввода-вывода и не хранит состояния, поэтому его
используют и HTTP-клиенты Jikan/AniList, и фасад ``AnimeApiClient``.
"""

from __future__ import annotations

from typing import Any

from backend.domain.entities.anime.anime import Anime


async def sanitize_query(query: str | None) -> str:
    """Убрать управляющие и лишние символы из поискового запроса."""
    if not query:
        return ""
    normalized = str(query).replace("\x00", " ").replace("\u0000", " ")
    normalized = " ".join(normalized.split())
    return normalized.strip()


async def normalize_numeric_id(value: Any) -> str:
    """Привести числовой идентификатор к положительной строке."""
    if isinstance(value, bool) or value is None:
        return ""
    try:
        numeric_value = int(value)
    except (TypeError, ValueError):
        return ""
    return str(numeric_value) if numeric_value > 0 else ""


async def normalize_episode_count(value: Any) -> int | None:
    """Привести число серий к положительному целому."""
    if isinstance(value, bool) or value is None:
        return None
    try:
        numeric_value = int(value)
    except (TypeError, ValueError):
        return None
    return numeric_value if numeric_value > 0 else None


async def build_anime_from_jikan_item(item: dict[str, Any]) -> Anime:
    """Собрать сущность ``Anime`` из элемента ответа Jikan."""
    title = str(item.get("title") or "").strip()
    original = str(item.get("title_english") or str(item.get("title") or "")).strip()
    return Anime(
        external_id=await normalize_numeric_id(item.get("mal_id")),
        title=title,
        original_title=original,
        description=item.get("synopsis"),
        genres=[
            str(genre.get("name") or "").strip()
            for genre in item.get("genres", [])
            if isinstance(genre, dict) and genre.get("name")
        ],
        year=item.get("year"),
        rating=item.get("score"),
        cover_url=item.get("images", {}).get("jpg", {}).get("image_url"),
        episode_count=await normalize_episode_count(item.get("episodes")),
    )


async def build_anime_from_anilist_item(
    item: dict[str, Any],
    fallback_to_anilist_id: bool,
) -> Anime:
    """Собрать сущность ``Anime`` из элемента ответа AniList."""
    title_data = item.get("title", {}) or {}
    average_score = item.get("averageScore")
    normalized_score = (average_score / 10) if isinstance(average_score, (int, float)) else None
    mal_id = await normalize_numeric_id(item.get("idMal"))
    anilist_id = await normalize_numeric_id(item.get("id"))
    external_id = mal_id or (anilist_id if fallback_to_anilist_id else "")
    romaji = str(title_data.get("romaji") or "").strip()
    english = str(title_data.get("english") or "").strip()

    return Anime(
        external_id=external_id,
        title=await pick_anilist_title(title_data),
        original_title=romaji or english,
        description=item.get("description"),
        genres=[str(genre).strip() for genre in (item.get("genres", []) or []) if genre],
        year=item.get("seasonYear"),
        rating=normalized_score,
        cover_url=item.get("coverImage", {}).get("large"),
        episode_count=await normalize_episode_count(item.get("episodes")),
    )


async def pick_anilist_title(title_data: dict[str, Any]) -> str:
    """Выбрать лучшее доступное название из ответа AniList."""
    for key in ("romaji", "english", "native"):
        value = str(title_data.get(key) or "").strip()
        if value:
            return value
    return "Unknown anime"


async def is_nsfw_jikan(item: dict) -> bool:
    """Определить взрослый контент по рейтингу Jikan."""
    rating_text = str(item.get("rating") or "").lower()
    nsfw_markers = ("hentai", "explicit", "porn", "rx")
    return any(marker in rating_text for marker in nsfw_markers)


async def is_nsfw_anilist(item: dict) -> bool:
    """Определить взрослый контент по метаданным AniList."""
    if bool(item.get("isAdult")):
        return True
    genres = item.get("genres", []) or []
    return any(str(genre).strip().lower() == "hentai" for genre in genres)


async def passes_filters(
    season_year: int | None,
    normalized_score: float | None,
    year_from: int | None,
    year_to: int | None,
    min_rating: int | None,
) -> bool:
    """Проверить, проходит ли аниме фильтры по году и рейтингу."""
    if year_from is not None and (season_year is None or season_year < year_from):
        return False
    if year_to is not None and (season_year is None or season_year > year_to):
        return False
    if min_rating is not None and (normalized_score is None or normalized_score < min_rating):
        return False
    return True
