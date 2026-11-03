"""Настройки входа, подтверждения почты и восстановления пароля."""

from __future__ import annotations

import os


def password_reset_expire_minutes() -> int:
    """Вернуть срок жизни ссылки восстановления пароля в минутах."""
    return int(os.getenv("PASSWORD_RESET_EXPIRE_MINUTES", "30"))


def email_verification_expire_minutes() -> int:
    """Вернуть срок жизни кода подтверждения почты в минутах."""
    return int(os.getenv("EMAIL_VERIFICATION_EXPIRE_MINUTES", "10"))


def auth_login_attempts_limit() -> int:
    """Вернуть лимит попыток входа за окно."""
    return int(os.getenv("AUTH_LOGIN_ATTEMPTS_LIMIT", "5"))


def auth_register_attempts_limit() -> int:
    """Вернуть лимит попыток регистрации за окно."""
    return int(os.getenv("AUTH_REGISTER_ATTEMPTS_LIMIT", "3"))


def auth_password_reset_attempts_limit() -> int:
    """Вернуть лимит попыток восстановления пароля за окно."""
    return int(os.getenv("AUTH_PASSWORD_RESET_ATTEMPTS_LIMIT", "3"))


def auth_verify_email_attempts_limit() -> int:
    """Вернуть лимит попыток подтверждения почты за окно."""
    return int(os.getenv("AUTH_VERIFY_EMAIL_ATTEMPTS_LIMIT", "10"))


def auth_verify_email_resend_limit() -> int:
    """Вернуть лимит повторных отправок кода подтверждения за окно."""
    return int(os.getenv("AUTH_VERIFY_EMAIL_RESEND_LIMIT", "3"))


def auth_api_refresh_attempts_limit() -> int:
    """Вернуть лимит продлений сессии мобильным клиентом за окно."""
    return int(os.getenv("AUTH_API_REFRESH_ATTEMPTS_LIMIT", "30"))


def auth_window_seconds() -> int:
    """Вернуть длину окна ограничения частоты в секундах."""
    return int(os.getenv("AUTH_WINDOW_SECONDS", "300"))


def account_lock_duration_seconds() -> int:
    """Вернуть длительность блокировки аккаунта после серии неудач в секундах."""
    return int(os.getenv("ACCOUNT_LOCK_DURATION_SECONDS", "1800"))


def google_client_id() -> str:
    """Вернуть OAuth client ID мобильного приложения для проверки ID-токена Google."""
    return os.getenv("GOOGLE_CLIENT_ID", "").strip()


def google_tokeninfo_url() -> str:
    """Вернуть адрес эндпоинта проверки ID-токена Google."""
    return os.getenv(
        "GOOGLE_TOKENINFO_URL",
        "https://oauth2.googleapis.com/tokeninfo",
    ).strip()
