"""Confirm password reset command."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ConfirmPasswordResetCommand:
    """Confirm password reset command.

    Attributes:
        token: Password reset token.
        password: New plain password.
    """

    token: str
    password: str
