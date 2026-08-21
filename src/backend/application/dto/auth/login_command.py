"""Login form payload."""

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
