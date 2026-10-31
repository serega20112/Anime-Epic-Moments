"""Настройки Kodik: API-токен, адрес и путь к хранилищу токенов."""

from __future__ import annotations

import os

from backend.config.sections.external._common import _clean_secret


def kodik_api_token() -> str | None:
    """Вернуть API-токен Kodik."""
    return _clean_secret(os.getenv("KODIK_API_TOKEN"))


def kodik_api_url() -> str:
    """Вернуть базовый адрес API Kodik."""
    return os.getenv("KODIK_API_URL", "https://kodik-api.com")


def kodik_tokens_path() -> str:
    """Вернуть путь к файлу публичных токенов Kodik."""
    return os.getenv("KODIK_TOKENS_PATH", "kodik_tokens/tokens.json")
