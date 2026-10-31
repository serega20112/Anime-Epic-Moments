"""Настройки JustWatch: партнёрский токен, адрес и локаль."""

from __future__ import annotations

import os

from backend.config.sections.external._common import _clean_secret


def justwatch_partner_token() -> str | None:
    """Вернуть партнёрский токен JustWatch."""
    return _clean_secret(os.getenv("JUSTWATCH_PARTNER_TOKEN"))


def justwatch_api_url() -> str:
    """Вернуть адрес контентного API JustWatch."""
    return os.getenv("JUSTWATCH_API_URL", "https://apis.justwatch.com/contentpartner/v2/content")


def justwatch_locale() -> str:
    """Вернуть локаль JustWatch."""
    return os.getenv("JUSTWATCH_LOCALE", "en_US")
