"""Каталоги аниме: внешние источники карточек и тайтлов.

Здесь живут клиенты справочников (AniList, Jikan, Shikimori) и агрегирующий
`AnimeApiClient`, который выбирает источник и отдаёт доменную сущность `Anime`.
Маппинг сырых ответов в домен — в подпакете `mapping`.

Видео-провайдеры (Kodik, AniLibria и другие) к каталогу отношения не имеют и живут в
`backend.infrastructure.external.video`.
"""

from __future__ import annotations

from .anilist_client import AniListAnimeClient, AniListSearchError
from .anime_api_client import AnimeApiClient
from .jikan_client import JikanAnimeClient
from .shikimori_client import ShikimoriClient

__all__ = [
    "AnimeApiClient",
    "AniListAnimeClient",
    "AniListSearchError",
    "JikanAnimeClient",
    "ShikimoriClient",
]
