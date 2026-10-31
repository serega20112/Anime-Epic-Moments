"""Настройки русскоязычных видео-источников.

Покрыты AniLibria, SameBand, AniBoom, Kinobox, AnimeGo, Sibnet и HDRezka: адрес,
таймаут и признак включения каждого провайдера.
"""

from __future__ import annotations

import os


def anilibria_api_url() -> str:
    """Вернуть базовый адрес API AniLibria."""
    return os.getenv("ANILIBRIA_API_URL", "https://anilibria.top/api/v1")


def sameband_enabled() -> bool:
    """Вернуть, включён ли SSR-источник SameBand."""
    return os.getenv("SAMEBAND_ENABLED", "0") == "1"


def sameband_base_url() -> str:
    """Вернуть адрес сайта SameBand."""
    return os.getenv("SAMEBAND_BASE_URL", "https://sameband.studio")


def sameband_timeout() -> float:
    """Вернуть таймаут запросов SameBand в секундах."""
    return float(os.getenv("SAMEBAND_TIMEOUT", "8"))


def aniboom_enabled() -> bool:
    """Вернуть, включён ли SSR-источник AniBoom."""
    return os.getenv("ANIBOOM_ENABLED", "0") == "1"


def aniboom_base_url() -> str:
    """Вернуть адрес плеера AniBoom."""
    return os.getenv("ANIBOOM_BASE_URL", "https://aniboom.one")


def aniboom_timeout() -> float:
    """Вернуть таймаут запросов AniBoom в секундах."""
    return float(os.getenv("ANIBOOM_TIMEOUT", "8"))


def kinobox_enabled() -> bool:
    """Вернуть, включён ли агрегатор Kinobox."""
    return os.getenv("KINOBOX_ENABLED", "1") == "1"


def kinobox_base_url() -> str:
    """Вернуть базовый адрес API Kinobox."""
    return os.getenv("KINOBOX_BASE_URL", "https://kinobox.tv")


def kinobox_timeout() -> float:
    """Вернуть таймаут запросов Kinobox в секундах."""
    return float(os.getenv("KINOBOX_TIMEOUT", "8"))


def animego_enabled() -> bool:
    """Вернуть, включён ли скрапер AnimeGo."""
    return os.getenv("ANIMEGO_ENABLED", "1") == "1"


def animego_base_url() -> str:
    """Вернуть адрес сайта AnimeGo."""
    return os.getenv("ANIMEGO_BASE_URL", "https://animego.org")


def animego_timeout() -> float:
    """Вернуть таймаут запросов AnimeGo в секундах."""
    return float(os.getenv("ANIMEGO_TIMEOUT", "10"))


def sibnet_enabled() -> bool:
    """Вернуть, включён ли экстрактор Sibnet."""
    return os.getenv("SIBNET_ENABLED", "1") == "1"


def sibnet_base_url() -> str:
    """Вернуть адрес видео-хостинга Sibnet."""
    return os.getenv("SIBNET_BASE_URL", "https://video.sibnet.ru")


def sibnet_timeout() -> float:
    """Вернуть таймаут запросов Sibnet в секундах."""
    return float(os.getenv("SIBNET_TIMEOUT", "8"))


def rezka_enabled() -> bool:
    """Вернуть, включён ли парсер HDRezka."""
    return os.getenv("REZKA_ENABLED", "0") == "1"


def rezka_base_url() -> str:
    """Вернуть адрес зеркала HDRezka."""
    return os.getenv("REZKA_BASE_URL", "https://rezka.ag")


def rezka_timeout() -> float:
    """Вернуть таймаут запросов HDRezka в секундах."""
    return float(os.getenv("REZKA_TIMEOUT", "10"))
