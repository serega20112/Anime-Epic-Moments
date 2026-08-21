"""Verify email command."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class VerifyEmailCommand:
    """Verify email command.

    Attributes:
        email: Normalized user email.
        code: Six digit verification code.
    """

    email: str
    code: str
