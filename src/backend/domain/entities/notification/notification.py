"""Сущность уведомления пользователя."""

from datetime import datetime

from backend.domain.clock import utc_now

KIND_HIGHLIGHT_LIKE = "highlight_like"
KIND_HIGHLIGHT_COMMENT = "highlight_comment"
KIND_NEW_FOLLOWER = "new_follower"
NOTIFICATION_KINDS = frozenset({KIND_HIGHLIGHT_LIKE, KIND_HIGHLIGHT_COMMENT, KIND_NEW_FOLLOWER})


class Notification:
    """Событие в центре уведомлений одного получателя."""

    def __init__(
        self,
        user_id: int,
        kind: str,
        text: str,
        actor_user_id: int | None = None,
        anime_id: int | None = None,
        highlight_id: int | None = None,
        is_read: bool = False,
        created_at: datetime | None = None,
        id: int | None = None,
    ):
        """Создать уведомление с заданными полями.

        Args:
            user_id: Идентификатор получателя уведомления.
            kind: Тип события из набора ``NOTIFICATION_KINDS``.
            text: Текст для показа человеку.
            actor_user_id: Идентификатор автора события либо None.
            anime_id: Идентификатор связанного тайтла либо None.
            highlight_id: Идентификатор связанного хайлайта либо None.
            is_read: Прочитано ли уведомление.
            created_at: Время создания, по умолчанию текущее UTC.
            id: Идентификатор записи в хранилище.
        """
        self.id = id
        self.user_id = user_id
        self.kind = kind
        self.text = text
        self.actor_user_id = actor_user_id
        self.anime_id = anime_id
        self.highlight_id = highlight_id
        self.is_read = bool(is_read)
        self.created_at = created_at or utc_now()
