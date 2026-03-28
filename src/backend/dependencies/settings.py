import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(PROJECT_ROOT / ".env")


def _build_default_database_url() -> str:
    user = os.getenv("POSTGRES_USER", "anime_epic_moments")
    password = os.getenv("POSTGRES_PASSWORD", "anime_epic_moments")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    database = os.getenv("POSTGRES_DB", "anime_epic_moments")
    return f"postgresql+psycopg://{user}:{password}@{host}:{port}/{database}"


def _normalize_database_url(value: str | None) -> str:
    raw_value = str(value or "").strip()
    if not raw_value:
        return _build_default_database_url()
    if raw_value.startswith("postgres://"):
        return f"postgresql+psycopg://{raw_value[len('postgres://') :]}"
    if raw_value.startswith("postgresql://") and "+psycopg" not in raw_value:
        return f"postgresql+psycopg://{raw_value[len('postgresql://') :]}"
    return raw_value


DEFAULT_DATABASE_URL = _normalize_database_url(os.getenv("DATABASE_URL"))
DEFAULT_DATABASE_AUTO_INIT = os.getenv("DATABASE_AUTO_INIT", "0")


class Settings:
    """
    Настройки приложения
    """

    secret_key: str = os.getenv("SECRET_KEY", "epic-anime-secret-key-123")
    database_url: str = DEFAULT_DATABASE_URL
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
    flask_host: str = os.getenv("FLASK_HOST", "0.0.0.0")
    flask_port: int = int(os.getenv("FLASK_PORT", "5000"))
    flask_debug: bool = os.getenv("FLASK_DEBUG", "0") == "1"
    max_request_bytes: int = int(os.getenv("MAX_REQUEST_BYTES", "1048576"))
    app_base_url: str = os.getenv("APP_BASE_URL", "http://127.0.0.1:5000")
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
    password_reset_expire_minutes: int = int(
        os.getenv("PASSWORD_RESET_EXPIRE_MINUTES", "30")
    )
