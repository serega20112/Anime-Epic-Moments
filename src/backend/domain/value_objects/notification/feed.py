"""Страница уведомлений мобильного клиента."""

from dataclasses import dataclass, field

from backend.domain.entities.notification.notification import Notification


@dataclass(frozen=True)
class NotificationFeedPage:
    """Одна страница уведомлений с числом непрочитанных.

    Attributes:
        items: Уведомления текущей страницы в порядке новых сначала.
        page: Номер страницы, начиная с единицы.
        per_page: Размер страницы.
        total: Общее число уведомлений в выборке.
        unread_count: Число непрочитанных уведомлений получателя.
        actor_names: Имена авторов событий по их идентификаторам.
    """

    items: list[Notification] = field(default_factory=list)
    page: int = 1
    per_page: int = 20
    total: int = 0
    unread_count: int = 0
    actor_names: dict[int, str] = field(default_factory=dict)
