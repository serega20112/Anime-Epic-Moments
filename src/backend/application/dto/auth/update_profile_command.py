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
        status: Optional status text shown under the username.
        show_watch_activity: Whether the viewing dynamics are public.
        show_recent_episodes: Whether recent episodes are public.
    """

    user_id: int
    username: str
    avatar_url: str | None = None
    status: str | None = None
    show_watch_activity: bool = True
    show_recent_episodes: bool = True
