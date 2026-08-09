"""Data transfer objects for authentication commands and queries."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class LoginCommand:
    """Login form payload.

    Attributes:
        email: Normalized user email.
        password: Plain password.
    """

    email: str
    password: str


@dataclass(frozen=True, slots=True)
class RegisterCommand:
    """Registration command requesting an email verification code.

    Attributes:
        email: Normalized user email.
        password: Plain password.
        username: Desired username.
        theme: UI theme preference.
    """

    email: str
    password: str
    username: str
    theme: str


@dataclass(frozen=True, slots=True)
class VerifyEmailCommand:
    """Verify email command.

    Attributes:
        email: Normalized user email.
        code: Six digit verification code.
    """

    email: str
    code: str


@dataclass(frozen=True, slots=True)
class ResendVerificationCommand:
    """Resend verification code command.

    Attributes:
        email: Normalized user email.
    """

    email: str


@dataclass(frozen=True, slots=True)
class RequestPasswordResetCommand:
    """Request password reset command.

    Attributes:
        email: Normalized user email.
        base_url: Origin used to build the reset link.
    """

    email: str
    base_url: str


@dataclass(frozen=True, slots=True)
class ConfirmPasswordResetCommand:
    """Confirm password reset command.

    Attributes:
        token: Password reset token.
        password: New plain password.
    """

    token: str
    password: str


@dataclass(frozen=True, slots=True)
class UpdateProfileCommand:
    """Update profile command.

    Attributes:
        user_id: Identifier of the authenticated user.
        username: Desired username.
        avatar_url: Optional avatar URL.
    """

    user_id: int
    username: str
    avatar_url: str | None = None
