"""Русскоязычные видео-источники: AniLibria, AniBoom, AnimeGo, HDRezka, Sibnet, SameBand, Kinobox.

Каждый провайдер знает только свой протокол и наружу отдаёт единые доменные сущности,
поэтому сценарии не различают источники. Доступность провайдера и таймаут приходят из
`config.sections.external`; отключённый провайдер возвращает пустой результат, а не ошибку.
"""

from __future__ import annotations

from .aniboom_provider import AniBoomProvider
from .anilibria_client import AniLibriaClient
from .animego_provider import AnimeGoProvider
from .hdrezka_provider import HDRezkaProvider
from .kinobox_provider import KinoboxProvider
from .sameband_provider import SamebandProvider
from .sibnet_provider import SibnetProvider

__all__ = [
    "AniBoomProvider",
    "AniLibriaClient",
    "AnimeGoProvider",
    "HDRezkaProvider",
    "KinoboxProvider",
    "SamebandProvider",
    "SibnetProvider",
]
