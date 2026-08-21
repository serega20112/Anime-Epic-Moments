"""Update profile command."""

from __future__ import annotations

from dataclasses import dataclass


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
