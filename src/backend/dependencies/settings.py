import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(PROJECT_ROOT / ".env")


def _build_default_database_url(*, async_mode: bool) -> str:
    user = os.getenv("POSTGRES_USER", "anime_epic_moments")
    password = os.getenv("POSTGRES_PASSWORD", "anime_epic_moments")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    database = os.getenv("POSTGRES_DB", "anime_epic_moments")
    scheme = "postgresql+asyncpg" if async_mode else "postgresql+psycopg"
    return f"{scheme}://{user}:{password}@{host}:{port}/{database}"


def _normalize_database_url(value: str | None, *, async_mode: bool) -> str:
    raw_value = str(value or "").strip()
    if not raw_value:
        return _build_default_database_url(async_mode=async_mode)
    if raw_value.startswith("postgres://"):
        raw_value = f"postgresql://{raw_value[len('postgres://') :]}"
    if async_mode:
        if raw_value.startswith("postgresql+asyncpg://"):
            return raw_value
        if raw_value.startswith("postgresql+psycopg://"):
            return f"postgresql+asyncpg://{raw_value[len('postgresql+psycopg://') :]}"
        if raw_value.startswith("postgresql://"):
            return f"postgresql+asyncpg://{raw_value[len('postgresql://') :]}"
        if raw_value.startswith("sqlite+aiosqlite:///"):
            return raw_value
        if raw_value.startswith("sqlite:///"):
            return f"sqlite+aiosqlite:///{raw_value[len('sqlite:///') :]}"
        return raw_value
    if raw_value.startswith("postgresql+psycopg://"):
        return raw_value
    if raw_value.startswith("postgresql+asyncpg://"):
        return f"postgresql+psycopg://{raw_value[len('postgresql+asyncpg://') :]}"
    if raw_value.startswith("postgresql://"):
        return f"postgresql+psycopg://{raw_value[len('postgresql://') :]}"
    if raw_value.startswith("sqlite+aiosqlite:///"):
        return f"sqlite:///{raw_value[len('sqlite+aiosqlite:///') :]}"
    return raw_value


DEFAULT_DATABASE_SYNC_URL = _normalize_database_url(
    os.getenv("DATABASE_URL"),
    async_mode=False,
)
DEFAULT_DATABASE_URL = _normalize_database_url(
    os.getenv("DATABASE_URL"),
    async_mode=True,
)
DEFAULT_DATABASE_AUTO_INIT = os.getenv("DATABASE_AUTO_INIT", "0")


class Settings:
    """
    Настройки приложения
    """

    secret_key: str = os.getenv("SECRET_KEY", "epic-anime-secret-key-123")
    database_url: str = DEFAULT_DATABASE_URL
    database_sync_url: str = DEFAULT_DATABASE_SYNC_URL
    database_auto_init: bool = DEFAULT_DATABASE_AUTO_INIT == "1"
    redis_enabled: bool = os.getenv("REDIS_ENABLED", "1") == "1"
    redis_required: bool = os.getenv("REDIS_REQUIRED", "0") == "1"
    redis_url: str | None = (
        os.getenv("REDIS_URL", "redis://localhost:6379/0")
        if redis_enabled
        else None
    )
    hf_token: str | None = os.getenv("HF_TOKEN")
    hf_provider: str | None = os.getenv("HF_PROVIDER", "fireworks-ai")
    hf_model: str = os.getenv("HF_MODEL", "openai/gpt-oss-120b")
    hf_api_url: str = os.getenv(
        "HF_API_URL", "https://router.huggingface.co/v1/chat/completions"
    )
    kodik_api_token: str | None = os.getenv("KODIK_API_TOKEN")
    kodik_api_url: str = os.getenv("KODIK_API_URL", "https://kodik-api.com")
    anilibria_api_url: str = os.getenv(
        "ANILIBRIA_API_URL", "https://anilibria.top/api/v1"
    )
    youtube_api_key: str | None = os.getenv("YOUTUBE_API_KEY")
    youtube_api_url: str = os.getenv(
        "YOUTUBE_API_URL", "https://www.googleapis.com/youtube/v3"
    )
    youtube_allowed_channel_ids: list[str] = [
        item.strip()
        for item in os.getenv("YOUTUBE_ALLOWED_CHANNEL_IDS", "").split(",")
        if item.strip()
    ]
    justwatch_partner_token: str | None = os.getenv("JUSTWATCH_PARTNER_TOKEN")
    justwatch_api_url: str = os.getenv(
        "JUSTWATCH_API_URL", "https://apis.justwatch.com/contentpartner/v2/content"
    )
    justwatch_locale: str = os.getenv("JUSTWATCH_LOCALE", "en_US")
    telegram_support_bot_token: str | None = os.getenv("TELEGRAM_SUPPORT_BOT_TOKEN")
    telegram_support_api_url: str = os.getenv(
        "TELEGRAM_SUPPORT_API_URL", "https://api.telegram.org"
    )
    telegram_support_admin_chat_ids: list[str] = [
        item.strip()
        for item in os.getenv("TELEGRAM_SUPPORT_ADMIN_CHAT_IDS", "").split(",")
        if item.strip()
    ]
    support_email_to: list[str] = [
        item.strip()
        for item in os.getenv("SUPPORT_EMAIL_TO", "").split(",")
        if item.strip()
    ]
    flask_host: str = os.getenv("FLASK_HOST", "0.0.0.0")
    flask_port: int = int(os.getenv("FLASK_PORT", "5000"))
    flask_debug: bool = os.getenv("FLASK_DEBUG", "0") == "1"
    max_request_bytes: int = int(os.getenv("MAX_REQUEST_BYTES", "1048576"))
    app_base_url: str = os.getenv("APP_BASE_URL", "http://127.0.0.1:5000")
    app_allowed_origins: list[str] = [
        item.strip()
        for item in os.getenv("APP_ALLOWED_ORIGINS", "").split(",")
        if item.strip()
    ]
    cookie_secure: bool = os.getenv("COOKIE_SECURE", "0") == "1"
    cookie_samesite: str = os.getenv("COOKIE_SAMESITE", "Lax")
    cookie_domain: str | None = os.getenv("COOKIE_DOMAIN") or None
    access_token_expire_minutes: int = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
    )
    refresh_token_expire_days: int = int(
        os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "30")
    )
    smtp_host: str | None = os.getenv("SMTP_HOST")
    smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
    smtp_username: str | None = os.getenv("SMTP_USERNAME")
    smtp_password: str | None = os.getenv("SMTP_PASSWORD")
    smtp_from_email: str | None = os.getenv("SMTP_FROM_EMAIL")
    smtp_use_tls: bool = os.getenv("SMTP_USE_TLS", "1") == "1"
    email_verification_expire_minutes: int = int(
        os.getenv("EMAIL_VERIFICATION_EXPIRE_MINUTES", "10")
    )
    password_reset_expire_minutes: int = int(
        os.getenv("PASSWORD_RESET_EXPIRE_MINUTES", "30")
    )
