"""Настройки 18+ видео-источников.

Hanime (включая proxy и Cloudflare-куки), Eporner и Hentaigasm: адрес, таймаут и
признак включения; управляются каждый своим флагом.
"""

from __future__ import annotations

import os


def hanime_enabled() -> bool:
    """Вернуть, включён ли источник Hanime.tv."""
    return os.getenv("HANIME_ENABLED", "1") == "1"


def hanime_base_url() -> str:
    """Вернуть базовый адрес API Hanime."""
    return os.getenv("HANIME_BASE_URL", "https://hanime.tv")


def hanime_timeout() -> float:
    """Вернуть таймаут запросов Hanime в секундах."""
    return float(os.getenv("HANIME_TIMEOUT", "10"))


def hanime_proxy() -> str:
    """Вернуть необязательный прокси для доступа к Hanime."""
    return os.getenv("HANIME_PROXY", "")


def hanime_cf_clearance() -> str:
    """Вернуть cookie ``cf_clearance`` Cloudflare для Hanime."""
    return os.getenv("HANIME_CF_CLEARANCE", "")


def hanime_user_agent() -> str:
    """Вернуть User-Agent, привязанный к cookie ``cf_clearance``."""
    return os.getenv(
        "HANIME_USER_AGENT",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    )


def eporner_enabled() -> bool:
    """Вернуть, включён ли 18+ источник Eporner."""
    return os.getenv("EPORNER_ENABLED", "1") == "1"


def eporner_base_url() -> str:
    """Вернуть базовый адрес API Eporner."""
    return os.getenv("EPORNER_BASE_URL", "https://www.eporner.com")


def eporner_timeout() -> float:
    """Вернуть таймаут запросов Eporner в секундах."""
    return float(os.getenv("EPORNER_TIMEOUT", "10"))


def hentaigasm_enabled() -> bool:
    """Вернуть, включён ли 18+ источник Hentaigasm."""
    return os.getenv("HENTAIGASM_ENABLED", "1") == "1"


def hentaigasm_base_url() -> str:
    """Вернуть адрес сайта Hentaigasm."""
    return os.getenv("HENTAIGASM_BASE_URL", "https://hentaigasm.com")


def hentaigasm_timeout() -> float:
    """Вернуть таймаут запросов Hentaigasm в секундах."""
    return float(os.getenv("HENTAIGASM_TIMEOUT", "10"))
