"""Параметры страницы уведомлений мобильного клиента."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class NotificationsQuery:
    """Запрос уведомлений получателя с постраничной выдачей.

    Attributes:
        user_id: Идентификатор получателя уведомлений.
        page: Номер страницы, начиная с единицы.
        per_page: Размер страницы.
    """

    user_id: int
    page: int = 1
    per_page: int = 20
