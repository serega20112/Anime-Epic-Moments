"""Resend verification code command."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ResendVerificationCommand:
    """Resend verification code command.

    Attributes:
        email: Normalized user email.
    """

    email: str
