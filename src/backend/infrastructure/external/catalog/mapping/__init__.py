"""Преобразование ответов каталогов в доменные сущности.

Маппинг отделён от HTTP-клиентов: клиент отвечает за запрос, кэш и разбор JSON, а эти
функции — за то, чтобы из чужого протокола получилась корректная сущность `Anime` со
всеми проверками домена. Здесь же нормализация сырых полей (числовые id, количество
серий) и признаки 18+ контента для фильтров.
"""

from __future__ import annotations

from .anime import (
    build_anime_from_anilist_item,
    build_anime_from_jikan_item,
    is_nsfw_anilist,
    is_nsfw_jikan,
    normalize_episode_count,
    normalize_numeric_id,
    passes_filters,
    pick_anilist_title,
    sanitize_query,
)

__all__ = [
    "build_anime_from_anilist_item",
    "build_anime_from_jikan_item",
    "is_nsfw_anilist",
    "is_nsfw_jikan",
    "normalize_episode_count",
    "normalize_numeric_id",
    "passes_filters",
    "pick_anilist_title",
    "sanitize_query",
]
