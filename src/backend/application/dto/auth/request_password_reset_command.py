"""Request password reset command."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RequestPasswordResetCommand:
    """Request password reset command.

    Attributes:
        email: Normalized user email.
        base_url: Origin used to build the reset link.
    """

    email: str
    base_url: str
