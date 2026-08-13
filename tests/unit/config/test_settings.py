from __future__ import annotations

import importlib

import dotenv

from backend.config import settings as settings_module


def test_settings_use_expected_defaults(monkeypatch):
    """Проверяем, что Settings использует дефолты, когда env-переменные не заданы."""
    with monkeypatch.context() as patch:
        patch.setattr(dotenv, "load_dotenv", lambda *args, **kwargs: None)
        for name in (
                "SECRET_KEY",
                "DATABASE_URL",
                "POSTGRES_DB",
                "POSTGRES_USER",
                "POSTGRES_PASSWORD",
                "POSTGRES_HOST",
                "POSTGRES_PORT",
                "HF_PROVIDER",
                "YOUTUBE_ALLOWED_CHANNEL_IDS",
                "APP_PORT",
                "APP_DEBUG",
                "REDIS_ENABLED",
                "REDIS_URL",
                "COOKIE_SECURE",
                "COOKIE_SAMESITE",
                "MAX_REQUEST_BYTES",
                "ACCESS_TOKEN_EXPIRE_MINUTES",
                "REFRESH_TOKEN_EXPIRE_DAYS",
                "SMTP_USE_TLS",
                "EMAIL_VERIFICATION_EXPIRE_MINUTES",
        ):
            patch.delenv(name, raising=False)
        patch.setenv("SECRET_KEY", "generated-in-debug")
        importlib.reload(settings_module)

        assert settings_module.Settings.secret_key == "generated-in-debug"
        assert settings_module.Settings.secret_key != "epic-anime-secret-key-123"
        assert settings_module.Settings.database_url == (
            "postgresql+asyncpg://anime_epic_moments:anime_epic_moments@localhost:5432/anime_epic_moments"
        )
        assert settings_module.Settings.database_auto_init is False
        assert settings_module.Settings.redis_enabled is True
        assert settings_module.Settings.redis_url == "redis://localhost:6379/0"
        assert settings_module.Settings.hf_provider == "fireworks-ai"
        assert settings_module.Settings.youtube_allowed_channel_ids == []
        assert settings_module.Settings.app_port == 5000
        assert settings_module.Settings.app_debug is False
        assert settings_module.Settings.max_request_bytes == 1048576
        assert settings_module.Settings.cookie_secure is False
        assert settings_module.Settings.cookie_samesite == "Lax"
        assert settings_module.Settings.access_token_expire_minutes == 30
        assert settings_module.Settings.refresh_token_expire_days == 30
        assert settings_module.Settings.smtp_use_tls is True
        assert settings_module.Settings.email_verification_expire_minutes == 10

    importlib.reload(settings_module)


def test_settings_require_secret_key_outside_debug(monkeypatch):
    """Проверяем, что вне debug-режима отсутствие SECRET_KEY приводит к ошибке."""
    with monkeypatch.context() as patch:
        patch.setattr(dotenv, "load_dotenv", lambda *args, **kwargs: None)
        patch.delenv("SECRET_KEY", raising=False)
        patch.delenv("APP_DEBUG", raising=False)
        try:
            importlib.reload(settings_module)
        except RuntimeError:
            assert True
        else:
            assert False, "Expected RuntimeError when SECRET_KEY is missing in production"
            assert False

    importlib.reload(settings_module)


def test_settings_parse_env_values(monkeypatch):
    """Проверяем, что Settings преобразует env-значения в числа, bool и списки."""
    with monkeypatch.context() as patch:
        patch.setattr(dotenv, "load_dotenv", lambda *args, **kwargs: None)
        patch.setenv("SECRET_KEY", "custom-secret")
        patch.setenv("DATABASE_URL", "postgres://user:pass@db:5432/app")
        patch.setenv("HF_PROVIDER", "hf-provider")
        patch.setenv("YOUTUBE_ALLOWED_CHANNEL_IDS", " channel-1 , channel-2 ")
        patch.setenv("APP_PORT", "7001")
        patch.setenv("APP_DEBUG", "1")
        patch.setenv("REDIS_URL", "redis://redis:6379/1")
        patch.setenv("COOKIE_SECURE", "1")
        patch.setenv("COOKIE_SAMESITE", "Strict")
        patch.setenv("MAX_REQUEST_BYTES", "2048")
        patch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "45")
        patch.setenv("REFRESH_TOKEN_EXPIRE_DAYS", "15")
        patch.setenv("SMTP_USE_TLS", "0")
        patch.setenv("EMAIL_VERIFICATION_EXPIRE_MINUTES", "20")
        patch.setenv("DATABASE_AUTO_INIT", "0")
        importlib.reload(settings_module)

        assert settings_module.Settings.secret_key == "custom-secret"
        assert settings_module.Settings.database_url == "postgresql+asyncpg://user:pass@db:5432/app"
        assert settings_module.Settings.database_auto_init is False
        assert settings_module.Settings.hf_provider == "hf-provider"
        assert settings_module.Settings.youtube_allowed_channel_ids == ["channel-1", "channel-2"]
        assert settings_module.Settings.app_port == 7001
        assert settings_module.Settings.app_debug is True
        assert settings_module.Settings.redis_url == "redis://redis:6379/1"
        assert settings_module.Settings.cookie_secure is True
        assert settings_module.Settings.cookie_samesite == "Strict"
        assert settings_module.Settings.max_request_bytes == 2048
        assert settings_module.Settings.access_token_expire_minutes == 45
        assert settings_module.Settings.refresh_token_expire_days == 15
        assert settings_module.Settings.smtp_use_tls is False
        assert settings_module.Settings.email_verification_expire_minutes == 20

    importlib.reload(settings_module)


def test_settings_builds_database_url_from_postgres_parts(monkeypatch):
    """Проверяем, что Settings собирает DATABASE_URL из POSTGRES_* переменных, если он не задан явно."""
    with monkeypatch.context() as patch:
        patch.setattr(dotenv, "load_dotenv", lambda *args, **kwargs: None)
        patch.delenv("DATABASE_URL", raising=False)
        patch.setenv("POSTGRES_DB", "anime_db")
        patch.setenv("POSTGRES_USER", "anime_user")
        patch.setenv("POSTGRES_PASSWORD", "anime_password")
        patch.setenv("POSTGRES_HOST", "postgres")
        patch.setenv("POSTGRES_PORT", "5433")
        patch.delenv("DATABASE_AUTO_INIT", raising=False)
        importlib.reload(settings_module)

        assert settings_module.Settings.database_url == (
            "postgresql+asyncpg://anime_user:anime_password@postgres:5433/anime_db"
        )
        assert settings_module.Settings.database_auto_init is False

    importlib.reload(settings_module)
