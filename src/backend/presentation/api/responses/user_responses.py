"""Модели ответов публичного профиля мобильного клиента."""

from __future__ import annotations

from pydantic import BaseModel


class MobileProfileResponse(BaseModel):
    """Профиль пользователя для мобильного клиента.

    Почта в публичный профиль не входит: она приватна и доступна только
    владельцу через отдельный маршрут. Поля ``google_linked`` и
    ``email_verified`` отражают состояние учётной записи.

    Attributes:
        id: Идентификатор пользователя.
        username: Отображаемое имя.
        avatar_url: Ссылка на аватар либо None.
        bio: Статус-описание профиля либо None.
        highlights_count: Число хайлайтов автора.
        followers_count: Число подписчиков.
        following_count: Число подписок.
        is_followed: Подписан ли текущий зритель на владельца профиля.
        google_linked: Привязан ли аккаунт к Google.
        email_verified: Подтверждена ли почта.
    """

    id: int
    username: str
    avatar_url: str | None = None
    bio: str | None = None
    highlights_count: int = 0
    followers_count: int = 0
    following_count: int = 0
    is_followed: bool = False
    google_linked: bool = False
    email_verified: bool = True
