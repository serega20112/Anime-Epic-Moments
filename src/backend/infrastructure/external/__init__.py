"""Фасад внешних интеграций: клиенты провайдеров данных и видео-источников.

Переэкспортирует только то, что действительно является внешней интеграцией. Почтовые
и Telegram-отправители живут в `backend.infrastructure.notifications`, а порты
интерфейсов — в `backend.application.interface.services`: выставлять их отсюда означало
бы смешать разные ответственности в одном пространстве имён.
"""

from __future__ import annotations

from backend.infrastructure.external.catalog import AnimeApiClient, ShikimoriClient
from backend.infrastructure.external.video import (
    JustWatchClient,
    YouTubeClient,
)
from backend.infrastructure.external.video.adult import (
    EpornerProvider,
    HanimeProvider,
    HentaigasmProvider,
)
from backend.infrastructure.external.video.kodik import KodikClient
from backend.infrastructure.external.video.ru import (
    AniBoomProvider,
    AniLibriaClient,
    AnimeGoProvider,
    HDRezkaProvider,
    KinoboxProvider,
    SamebandProvider,
    SibnetProvider,
)

__all__ = [
    "AniBoomProvider",
    "AniLibriaClient",
    "AnimeApiClient",
    "AnimeGoProvider",
    "EpornerProvider",
    "HDRezkaProvider",
    "HanimeProvider",
    "HentaigasmProvider",
    "JustWatchClient",
    "KinoboxProvider",
    "KodikClient",
    "SamebandProvider",
    "ShikimoriClient",
    "SibnetProvider",
    "YouTubeClient",
]
