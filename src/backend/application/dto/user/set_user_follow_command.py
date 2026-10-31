"""Команда подписки и отписки от пользователя."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SetUserFollowCommand:
    """Команда изменения подписки между пользователями.

    Attributes:
        follower_user_id: Идентификатор подписчика.
        followed_user_id: Идентификатор пользователя, на которого подписываются.
        follow: True — подписаться, False — отписаться.
    """

    follower_user_id: int
    followed_user_id: int
    follow: bool
