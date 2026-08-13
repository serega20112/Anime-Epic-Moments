"""HTTP server and web application settings."""

from __future__ import annotations

import os


def app_host() -> str:
    """Return the bind host for the web server.

    Returns:
        str: Bind host.
    """
    return os.getenv("APP_HOST", "0.0.0.0")


def app_port() -> int:
    """Return the bind port for the web server.

    Returns:
        int: Bind port.
    """
    return int(os.getenv("APP_PORT", "5000"))


def app_debug() -> bool:
    """Return whether debug mode is enabled.

    Returns:
        bool: True when APP_DEBUG is enabled.
    """
    return os.getenv("APP_DEBUG", "0") == "1"


def log_level() -> str:
    """Return the application log level.

    Returns:
        str: Log level name.
    """
    return os.getenv("LOG_LEVEL", "INFO")


def max_request_bytes() -> int:
    """Return the maximum allowed request payload size.

    Returns:
        int: Maximum request size in bytes.
    """
    return int(os.getenv("MAX_REQUEST_BYTES", "1048576"))


def app_base_url() -> str:
    """Return the public base URL of the application.

    Returns:
        str: Application base URL.
    """
    return os.getenv("APP_BASE_URL", "http://127.0.0.1:5000")


def app_allowed_origins() -> list[str]:
    """Return the allowed CORS origins.

    Returns:
        list[str]: Allowed origins.
    """
    return [
        item.strip() for item in os.getenv("APP_ALLOWED_ORIGINS", "").split(",") if item.strip()
    ]