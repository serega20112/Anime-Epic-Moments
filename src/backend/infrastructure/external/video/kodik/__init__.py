"""Kodik: клиент API, хранилище токенов и маппинг ответов.

Kodik отдаёт и переводы, и эпизоды, и ссылки на плеер, поэтому выделен в отдельный
подпакет: `client` — HTTP, `token_store` — пул токенов из файла конфигурации,
`mapping` — превращение ответа в доменные сущности.
"""

from __future__ import annotations

from .client import KodikClient
from .mapping import map_kodik_translations_to_episodes
from .token_store import KodikTokenStore, decrypt_token, encrypt_token

__all__ = [
    "KodikClient",
    "KodikTokenStore",
    "decrypt_token",
    "encrypt_token",
    "map_kodik_translations_to_episodes",
]
