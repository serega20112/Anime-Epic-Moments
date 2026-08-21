"""Map incoming auth form data to application command DTOs.

All HTTP form parsing, normalization and validation live here so that route
handlers stay thin and only orchestrate use case execution.
"""

from __future__ import annotations

from backend.application.dto.auth import (
    ConfirmPasswordResetCommand,
    LoginCommand,
    RegisterCommand,
    RequestPasswordResetCommand,
    ResendVerificationCommand,
    UpdateProfileCommand,
    VerifyEmailCommand,
)
from backend.domain.policies.user_credentials_policy import normalize_email

EMAIL_MAX_LENGTH = 254
PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_LENGTH = 128
USERNAME_MAX_LENGTH = 20
VERIFICATION_CODE_DIGITS = 6

THEMES = {"neon", "dark", "light", "rose"}
DEFAULT_THEME = "neon"


class FormValidationError(ValueError):
    """Raised when an HTML form fails validation."""


async def _field_text(form: dict, name: str) -> str:
    """Return a stripped string form field.

    Args:
        form: Parsed form data.
        name: Field name.

    Returns:
        str: Stripped field value.
    """
    return str(form.get(name) or "").strip()


async def _normalize_email(value: object) -> str:
    return normalize_email(value)


async def _normalize_theme(value: object) -> str:
    normalized = str(value or "").strip().lower()
    return normalized if normalized in THEMES else DEFAULT_THEME


async def _extract_digits(value: object) -> str:
    return "".join(character for character in str(value or "") if character.isdigit())


async def _require_valid_email(email: str) -> None:
    if not email or len(email) > EMAIL_MAX_LENGTH:
        raise FormValidationError("Некорректный email")


async def _clean_optional(value: object) -> str | None:
    cleaned = str(value or "").strip()
    return cleaned or None


async def map_login_command(form: dict) -> LoginCommand:
    """Validate and build a login command from form data.

    Args:
        form: Parsed form data.

    Returns:
        LoginCommand: Validated login command.

    Raises:
        FormValidationError: If email or password is missing or email is too long.
    """
    email = await _field_text(form, "email").lower()
    password = str(form.get("password") or "")
    if not email or len(email) > EMAIL_MAX_LENGTH or not password:
        raise FormValidationError("Некорректные данные для входа")
    return LoginCommand(email=email, password=password)


async def map_register_command(form: dict) -> RegisterCommand:
    """Validate and build a registration command from form data.

    Args:
        form: Parsed form data.

    Returns:
        RegisterCommand: Validated registration command.

    Raises:
        FormValidationError: If any required field is invalid.
    """
    email = await _normalize_email(form.get("email"))
    password = str(form.get("password") or "")
    username = await _field_text(form, "username")
    theme = await _normalize_theme(form.get("theme"))
    await _require_valid_email(email)
    if len(password) < PASSWORD_MIN_LENGTH or len(password) > PASSWORD_MAX_LENGTH:
        raise FormValidationError("Пароль должен быть не короче 8 символов")
    if not username or len(username) > USERNAME_MAX_LENGTH:
        raise FormValidationError("Некорректный username")
    return RegisterCommand(
        email=email,
        password=password,
        username=username,
        theme=theme,
    )


async def map_verify_email_command(form: dict) -> VerifyEmailCommand:
    """Validate and build an email verification command from form data.

    Args:
        form: Parsed form data.

    Returns:
        VerifyEmailCommand: Validated verification command.

    Raises:
        FormValidationError: If email or code is invalid.
    """
    email = await _normalize_email(form.get("email"))
    code = await _extract_digits(form.get("code"))
    await _require_valid_email(email)
    if len(code) != VERIFICATION_CODE_DIGITS:
        raise FormValidationError("Код подтверждения должен содержать 6 цифр")
    return VerifyEmailCommand(email=email, code=code)


async def map_resend_verification_command(form: dict) -> ResendVerificationCommand:
    """Validate and build a resend verification command from form data.

    Args:
        form: Parsed form data.

    Returns:
        ResendVerificationCommand: Validated command.

    Raises:
        FormValidationError: If email is missing or invalid.
    """
    email = await _normalize_email(form.get("email"))
    await _require_valid_email(email)
    return ResendVerificationCommand(email=email)


async def map_request_password_reset_command(
    form: dict, *, base_url: str
) -> RequestPasswordResetCommand:
    """Validate and build a password reset request command from form data.

    Args:
        form: Parsed form data.
        base_url: Origin used to build the reset link.

    Returns:
        RequestPasswordResetCommand: Validated command.

    Raises:
        FormValidationError: If email is missing or invalid.
    """
    email = await _normalize_email(form.get("email"))
    await _require_valid_email(email)
    return RequestPasswordResetCommand(email=email, base_url=base_url)


async def map_confirm_password_reset_command(form: dict) -> ConfirmPasswordResetCommand:
    """Validate and build a password reset confirmation command from form data.

    Args:
        form: Parsed form data.

    Returns:
        ConfirmPasswordResetCommand: Validated command.

    Raises:
        FormValidationError: If password or repeat do not match requirements.
    """
    token = await _field_text(form, "token")
    password = str(form.get("password") or "")
    password_repeat = str(form.get("password_repeat") or "")
    if password != password_repeat:
        raise FormValidationError("Пароли не совпадают")
    if len(password) < PASSWORD_MIN_LENGTH or len(password) > PASSWORD_MAX_LENGTH:
        raise FormValidationError("Пароль должен быть не короче 8 символов")
    return ConfirmPasswordResetCommand(token=token, password=password)


async def map_update_profile_command(form: dict, *, user_id: int) -> UpdateProfileCommand:
    """Validate and build a profile update command from form data.

    Args:
        form: Parsed form data.
        user_id: Authenticated user identifier.

    Returns:
        UpdateProfileCommand: Validated command.
    """
    username = await _field_text(form, "username")
    avatar_url = await _clean_optional(form.get("avatar_url"))
    return UpdateProfileCommand(
        user_id=user_id,
        username=username,
        avatar_url=avatar_url,
    )
