"""Настройки проксирования медиа: вышестоящий proxy для потоков."""

from __future__ import annotations

import os


def media_proxy_upstream_proxy() -> str:
    """Вернуть необязательный прокси для потового медиа из вышестоящего источника."""
    return os.getenv("MEDIA_PROXY_PROXY", "")
