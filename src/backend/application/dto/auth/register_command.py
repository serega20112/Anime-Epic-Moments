"""Registration command requesting an email verification code."""

from __future__ import annotations

from dataclasses import dataclass


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
