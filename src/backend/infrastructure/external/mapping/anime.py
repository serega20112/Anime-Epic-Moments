"""Pure mapping helpers between provider payloads and the domain Anime entity.

The functions in this module perform no I/O and own no state, so they can be
shared by the Jikan/AniList HTTP clients and the orchestrating
``AnimeApiClient`` facade without coupling either to a particular client.
"""

from __future__ import annotations

from typing import Any

from backend.domain.anime.entity import Anime


async def sanitize_query(query: str | None) -> str:
    """Strip control and redundant characters from a search query.

    Args:
        query: Raw search query.

    Returns:
        str: Sanitized query.
    """
    if not query:
        return ""
    normalized = str(query).replace("\x00", " ").replace("\u0000", " ")
    normalized = " ".join(normalized.split())
    return normalized.strip()


async def normalize_numeric_id(value: Any) -> str:
    """Normalize a numeric id to a positive string.

    Args:
        value: Raw id value.

    Returns:
        str: Normalized id or empty string.
    """
    if isinstance(value, bool) or value is None:
        return ""
    try:
        numeric_value = int(value)
    except (TypeError, ValueError):
        return ""
    return str(numeric_value) if numeric_value > 0 else ""


async def normalize_episode_count(value: Any) -> int | None:
    """Normalize an episode count to a positive integer.

    Args:
        value: Raw episode count.

    Returns:
        int | None: Normalized count or None.
    """
    if isinstance(value, bool) or value is None:
        return None
    try:
        numeric_value = int(value)
    except (TypeError, ValueError):
        return None
    return numeric_value if numeric_value > 0 else None


async def build_anime_from_jikan_item(item: dict[str, Any]) -> Anime:
    """Build a domain Anime from a Jikan item dict.

    Args:
        item: Jikan API item.

    Returns:
        Anime: Domain anime.
    """
    return Anime(
        external_id=await normalize_numeric_id(item.get("mal_id")),
        title=str(item.get("title") or "").strip(),
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
    """Build a domain Anime from an AniList item dict.

    Args:
        item: AniList API item.
        fallback_to_anilist_id: Whether to prefer the AniList id.

    Returns:
        Anime: Domain anime.
    """
    title_data = item.get("title", {}) or {}
    average_score = item.get("averageScore")
    normalized_score = (average_score / 10) if isinstance(average_score, (int, float)) else None
    mal_id = await normalize_numeric_id(item.get("idMal"))
    anilist_id = await normalize_numeric_id(item.get("id"))
    external_id = mal_id or (anilist_id if fallback_to_anilist_id else "")

    return Anime(
        external_id=external_id,
        title=await pick_anilist_title(title_data),
        description=item.get("description"),
        genres=[str(genre).strip() for genre in (item.get("genres", []) or []) if genre],
        year=item.get("seasonYear"),
        rating=normalized_score,
        cover_url=item.get("coverImage", {}).get("large"),
        episode_count=await normalize_episode_count(item.get("episodes")),
    )


async def pick_anilist_title(title_data: dict[str, Any]) -> str:
    """Pick the best available AniList title.

    Args:
        title_data: AniList title mapping.

    Returns:
        str: Chosen title.
    """
    for key in ("romaji", "english", "native"):
        value = str(title_data.get(key) or "").strip()
        if value:
            return value
    return "Unknown anime"


async def is_nsfw_jikan(item: dict) -> bool:
    """Detect NSFW content from a Jikan rating string.

    Args:
        item: Jikan API item.

    Returns:
        bool: True when the item is NSFW.
    """
    rating_text = str(item.get("rating") or "").lower()
    nsfw_markers = ("hentai", "explicit", "porn", "rx")
    return any(marker in rating_text for marker in nsfw_markers)


async def is_nsfw_anilist(item: dict) -> bool:
    """Detect NSFW content from AniList metadata.

    Args:
        item: AniList API item.

    Returns:
        bool: True when the item is NSFW.
    """
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
    """Check whether an anime passes year and rating filters.

    Args:
        season_year: Anime release season year.
        normalized_score: Normalized average score.
        year_from: Minimum season year or None.
        year_to: Maximum season year or None.
        min_rating: Minimum normalized rating or None.

    Returns:
        bool: True when the anime passes all filters.
    """
    if year_from is not None and (season_year is None or season_year < year_from):
        return False
    if year_to is not None and (season_year is None or season_year > year_to):
        return False
    if min_rating is not None and (normalized_score is None or normalized_score < min_rating):
        return False
    return True
