"""Постановка и снятие лайка с комментария в обсуждении."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SetAnimeCommentLikeCommand:
    """Команда изменения лайка комментария.

    Attributes:
        comment_id: Идентификатор комментария.
        user_id: Идентификатор действующего пользователя.
        liked: True — поставить лайк, False — снять.
    """

    comment_id: int
    user_id: int
    liked: bool
