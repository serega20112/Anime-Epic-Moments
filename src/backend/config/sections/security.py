"""Настройки безопасности и сроков жизни токенов."""

from __future__ import annotations

import os
import secrets


def _as_bool(value: str) -> bool:
    """Проверить, что сырое значение равно литералу ``1``.

    Args:
        value: Сырая строка окружения.

    Returns:
        bool: True, если строка равна ``1``.
    """
    return value == "1"


def secret_key() -> str:
    """Вернуть секретный ключ приложения.

    В продакшене (``APP_DEBUG=0``) ключ обязателен. В режиме отладки генерируется
    случайный ключ на процесс: этого достаточно локально, но значение не переживает
    перезапуск.

    Returns:
        str: Ключ подписи токенов и CSRF.

    Raises:
        RuntimeError: Если вне отладки переменная ``SECRET_KEY`` не задана.
    """
    value = os.getenv("SECRET_KEY")
    if value:
        return value
    if not app_debug():
        raise RuntimeError("SECRET_KEY must be set when APP_DEBUG=0")
    return secrets.token_urlsafe(48)


def app_debug() -> bool:
    """Вернуть, включён ли режим отладки."""
    return os.getenv("APP_DEBUG", "0") == "1"


def csrf_token_name() -> str:
    """Вернуть имя поля с CSRF-токеном."""
    return os.getenv("CSRF_TOKEN_NAME", "csrf_token")


def cookie_secure() -> bool:
    """Вернуть, помечаются ли cookie флагом Secure."""
    return _as_bool(os.getenv("COOKIE_SECURE", "0"))


def cookie_samesite() -> str:
    """Вернуть политику SameSite для cookie."""
    return os.getenv("COOKIE_SAMESITE", "Lax")


def cookie_domain() -> str | None:
    """Вернуть домен cookie или None, если он не задан."""
    return os.getenv("COOKIE_DOMAIN") or None


def access_token_expire_minutes() -> int:
    """Вернуть срок жизни access-токена в минутах."""
    return int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))


def refresh_token_expire_days() -> int:
    """Вернуть срок жизни refresh-токена в днях."""
    return int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "30"))


def hsts_max_age() -> int:
    """Вернуть HSTS max-age в секундах."""
    return int(os.getenv("HSTS_MAX_AGE", "63072000"))


def trusted_proxies() -> list[str]:
    """Вернуть список доверенных адресов обратного прокси.

    ``X-Forwarded-For`` учитывается, только если непосредственный пир сокета входит
    в один из этих IP-адресов или CIDR-сетей. Пустой список означает, что заголовок
    игнорируется всегда.

    Returns:
        list[str]: IP-адреса и сети доверенных прокси.
    """
    raw = os.getenv("TRUSTED_PROXIES", "")
    return [item.strip() for item in raw.split(",") if item.strip()]
