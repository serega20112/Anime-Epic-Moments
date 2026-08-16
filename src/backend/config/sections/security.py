"""Security and authentication token settings."""

from __future__ import annotations

import os
import secrets


def _as_bool(value: str) -> bool:
    """Return True when the raw value equals the literal "1".

    Args:
        value: Raw string to evaluate.

    Returns:
        bool: True for the literal "1".
    """
    return value == "1"


def secret_key() -> str:
    """Return the application secret key.

    A value must be supplied explicitly in production (APP_DEBUG=0). In debug
    mode a random key is generated per process, which is fine for local
    development but never stable across restarts.

    Returns:
        str: Secret key used for signing and CSRF.

    Raises:
        RuntimeError: When no SECRET_KEY is set outside debug mode.
    """
    value = os.getenv("SECRET_KEY")
    if value:
        return value
    if not app_debug():
        raise RuntimeError("SECRET_KEY must be set when APP_DEBUG=0")
    return secrets.token_urlsafe(48)


def app_debug() -> bool:
    """Return whether debug mode is enabled.

    Returns:
        bool: True when APP_DEBUG is enabled.
    """
    return os.getenv("APP_DEBUG", "0") == "1"


def csrf_token_name() -> str:
    """Return the CSRF token field name.

    Returns:
        str: CSRF token name.
    """
    return os.getenv("CSRF_TOKEN_NAME", "csrf_token")


def cookie_secure() -> bool:
    """Return whether cookies are marked Secure.

    Returns:
        bool: True when COOKIE_SECURE is enabled.
    """
    return _as_bool(os.getenv("COOKIE_SECURE", "0"))


def cookie_samesite() -> str:
    """Return the SameSite policy for cookies.

    Returns:
        str: SameSite value.
    """
    return os.getenv("COOKIE_SAMESITE", "Lax")


def cookie_domain() -> str | None:
    """Return the cookie domain.

    Returns:
        str | None: Cookie domain or None.
    """
    return os.getenv("COOKIE_DOMAIN") or None


def access_token_expire_minutes() -> int:
    """Return the access token lifetime in minutes.

    Returns:
        int: Access token lifetime.
    """
    return int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))


def refresh_token_expire_days() -> int:
    """Return the refresh token lifetime in days.

    Returns:
        int: Refresh token lifetime.
    """
    return int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "30"))


def hsts_max_age() -> int:
    """Return the HSTS max-age in seconds.

    Returns:
        int: HSTS max-age.
    """
    return int(os.getenv("HSTS_MAX_AGE", "63072000"))
