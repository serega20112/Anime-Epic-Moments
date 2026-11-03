"""Модели ответов центра уведомлений мобильного клиента."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from backend.presentation.api.responses.pagination import Page


class NotificationResponse(BaseModel):
    """Одно уведомление в JSON-представлении.

    Attributes:
        id: Идентификатор уведомления.
        kind: Тип события.
        text: Текст для показа человеку.
        actor_user_id: Идентификатор автора события либо None.
        actor_name: Имя автора либо None, когда автор неизвестен.
        anime_id: Идентификатор связанного тайтла либо None.
        highlight_id: Идентификатор связанного хайлайта либо None.
        is_read: Прочитано ли уведомление.
        created_at: Время события.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    kind: str
    text: str
    actor_user_id: int | None = None
    actor_name: str | None = None
    anime_id: int | None = None
    highlight_id: int | None = None
    is_read: bool = False
    created_at: datetime | None = None


class NotificationsPageResponse(Page[NotificationResponse]):
    """Страница уведомлений с числом непрочитанных.

    Attributes:
        unread_count: Число непрочитанных уведомлений получателя.
    """

    unread_count: int = 0


class NotificationsMarkedResponse(BaseModel):
    """Итог отметки уведомлений прочитанными.

    Attributes:
        marked: Число уведомлений, помеченных прочитанными.
    """

    marked: int
