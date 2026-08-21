"""Application configuration assembled from environment variable sections.

All values are read at class-body evaluation time by calling pure loader
functions from :mod:`backend.config.sections`, so re-importing this module
recomputes them from the current environment.
"""

from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv

from backend.config.sections import auth, database, external, redis_, security, server, validation
from backend.config.sections.security import secret_key

PROJECT_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(PROJECT_ROOT / ".env")


class Settings:
    """Application settings loaded from environment variables."""

    secret_key: str = secret_key()
    database_url: str = database.database_url()
    database_auto_init: bool = database.database_auto_init()
    redis_enabled: bool = redis_.redis_enabled()
    redis_required: bool = redis_.redis_required()
    redis_url: str | None = redis_.redis_url()
    openrouter_api_key: str | None = external.openrouter_api_key()
    openrouter_model: str = external.openrouter_model()
    openrouter_api_url: str = external.openrouter_api_url()
    hf_token: str | None = external.hf_token()
    hf_provider: str | None = external.hf_provider()
    hf_model: str = external.hf_model()
    hf_api_url: str = external.hf_api_url()
    google_api_key: str | None = external.google_api_key()
    google_model: str = external.google_model()
    google_api_url: str = external.google_api_url()
    kodik_api_token: str | None = external.kodik_api_token()
    kodik_api_url: str = external.kodik_api_url()
    kodik_tokens_path: str = external.kodik_tokens_path()
    anilibria_api_url: str = external.anilibria_api_url()
    sameband_enabled: bool = external.sameband_enabled()
    sameband_base_url: str = external.sameband_base_url()
    sameband_timeout: float = external.sameband_timeout()
    aniboom_enabled: bool = external.aniboom_enabled()
    aniboom_base_url: str = external.aniboom_base_url()
    aniboom_timeout: float = external.aniboom_timeout()
    youtube_api_key: str | None = external.youtube_api_key()
    youtube_api_url: str = external.youtube_api_url()
    youtube_allowed_channel_ids: list[str] = external.youtube_allowed_channel_ids()
    justwatch_partner_token: str | None = external.justwatch_partner_token()
    justwatch_api_url: str = external.justwatch_api_url()
    justwatch_locale: str = external.justwatch_locale()
    telegram_support_bot_token: str | None = external.telegram_support_bot_token()
    telegram_support_api_url: str = external.telegram_support_api_url()
    telegram_support_admin_chat_ids: list[str] = external.telegram_support_admin_chat_ids()
    support_email_to: list[str] = external.support_email_to()
    app_host: str = server.app_host()
    app_port: int = server.app_port()
    app_debug: bool = server.app_debug()
    max_request_bytes: int = server.max_request_bytes()
    app_base_url: str = server.app_base_url()
    app_allowed_origins: list[str] = server.app_allowed_origins()
    cookie_secure: bool = security.cookie_secure()
    cookie_samesite: str = security.cookie_samesite()
    cookie_domain: str | None = security.cookie_domain()
    access_token_expire_minutes: int = security.access_token_expire_minutes()
    refresh_token_expire_days: int = security.refresh_token_expire_days()
    smtp_host: str | None = external.smtp_host()
    smtp_port: int = external.smtp_port()
    smtp_username: str | None = external.smtp_username()
    smtp_password: str | None = external.smtp_password()
    smtp_from_email: str | None = external.smtp_from_email()
    smtp_use_tls: bool = external.smtp_use_tls()
    email_verification_expire_minutes: int = auth.email_verification_expire_minutes()
    password_reset_expire_minutes: int = auth.password_reset_expire_minutes()
    auth_login_attempts_limit: int = auth.auth_login_attempts_limit()
    auth_register_attempts_limit: int = auth.auth_register_attempts_limit()
    auth_password_reset_attempts_limit: int = auth.auth_password_reset_attempts_limit()
    auth_verify_email_attempts_limit: int = auth.auth_verify_email_attempts_limit()
    auth_verify_email_resend_limit: int = auth.auth_verify_email_resend_limit()
    auth_window_seconds: int = auth.auth_window_seconds()
    support_ticket_rate_limit: int = validation.support_ticket_rate_limit()
    highlight_comment_rate_limit: int = validation.highlight_comment_rate_limit()
    highlight_rate_window_seconds: int = validation.highlight_rate_window_seconds()
    log_level: str = server.log_level()
    account_lock_duration_seconds: int = auth.account_lock_duration_seconds()
    hsts_max_age: int = security.hsts_max_age()
    csrf_token_name: str = security.csrf_token_name()
    anime_query_limit_max: int = validation.anime_query_limit_max()
    anime_title_max_length: int = validation.anime_title_max_length()
    anime_description_max_length: int = validation.anime_description_max_length()
    anime_genre_hint_max_length: int = validation.anime_genre_hint_max_length()
    anime_autocomplete_limit_max: int = validation.anime_autocomplete_limit_max()
