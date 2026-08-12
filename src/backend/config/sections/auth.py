"""Authentication, email verification and password reset settings."""

from __future__ import annotations

import os


def password_reset_expire_minutes() -> int:
    """Return the password reset link lifetime in minutes.

    Returns:
        int: Password reset token lifetime.
    """
    return int(os.getenv("PASSWORD_RESET_EXPIRE_MINUTES", "30"))


def email_verification_expire_minutes() -> int:
    """Return the email verification code lifetime in minutes.

    Returns:
        int: Email verification code lifetime.
    """
    return int(os.getenv("EMAIL_VERIFICATION_EXPIRE_MINUTES", "10"))


def auth_login_attempts_limit() -> int:
    """Return the login attempts limit per window.

    Returns:
        int: Login attempts limit.
    """
    return int(os.getenv("AUTH_LOGIN_ATTEMPTS_LIMIT", "5"))


def auth_register_attempts_limit() -> int:
    """Return the register attempts limit per window.

    Returns:
        int: Register attempts limit.
    """
    return int(os.getenv("AUTH_REGISTER_ATTEMPTS_LIMIT", "3"))


def auth_password_reset_attempts_limit() -> int:
    """Return the password reset attempts limit per window.

    Returns:
        int: Password reset attempts limit.
    """
    return int(os.getenv("AUTH_PASSWORD_RESET_ATTEMPTS_LIMIT", "3"))


def auth_verify_email_attempts_limit() -> int:
    """Return the email verification attempts limit per window.

    Returns:
        int: Email verification attempts limit.
    """
    return int(os.getenv("AUTH_VERIFY_EMAIL_ATTEMPTS_LIMIT", "10"))


def auth_verify_email_resend_limit() -> int:
    """Return the email verification resend limit per window.

    Returns:
        int: Email verification resend limit.
    """
    return int(os.getenv("AUTH_VERIFY_EMAIL_RESEND_LIMIT", "3"))


def auth_window_seconds() -> int:
    """Return the rate limiting window in seconds.

    Returns:
        int: Rate limiting window.
    """
    return int(os.getenv("AUTH_WINDOW_SECONDS", "300"))


def account_lock_duration_seconds() -> int:
    """Return how long an account stays locked after repeated failures.

    Returns:
        int: Account lock duration in seconds.
    """
    return int(os.getenv("ACCOUNT_LOCK_DURATION_SECONDS", "1800"))