"""Видео-провайдеры: источники серий, переводов и плеерных ссылок.

Подпакет отвечает за то, что пользователь в итоге смотрит: поиск переводов, эпизодов и
playable-ссылок. Внутри — разделение по типу источника:

- `kodik` — Kodik с токенами и маппингом;
- `ru` — русскоязычные источники (AniLibria, AniBoom, AnimeGo, HDRezka, Sibnet,
  SameBand, Kinobox);
- `adult` — 18+ источники (Hanime, Eporner, Hentaigasm);
- `hls_proxy` — проксирование HLS и белый список хостов;
- `youtube_client`, `justwatch_client` — вспомогательные внешние сервисы.

Контракт провайдера источников (`WatchSourceProviderInterface`) объявлен в
`backend.application.interface.services` и оттуда же импортируется: инфраструктура не
переопределяет чужие интерфейсы и не заводит для них псевдонимов. Приоритет и выбор
«какой источник показать» решает application-сервис синхронизации источников.
"""

from __future__ import annotations

from .justwatch_client import JustWatchClient
from .youtube_client import YouTubeClient

__all__ = [
    "JustWatchClient",
    "YouTubeClient",
]
