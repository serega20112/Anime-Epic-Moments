"""Модели ответов JSON-маршрутов хайлайтов."""

from __future__ import annotations

from pydantic import BaseModel


class HighlightIdResponse(BaseModel):
    """Идентификатор хайлайта после создания или правки.

    Attributes:
        highlight_id: Идентификатор сохранённого хайлайта.
    """

    highlight_id: int | None = None


class HighlightLikeResponse(BaseModel):
    """Состояние лайка хайлайта после изменения.

    Attributes:
        highlight_id: Идентификатор хайлайта.
        liked: Итоговое состояние лайка.
        likes_count: Число лайков хайлайта.
    """

    highlight_id: int
    liked: bool
    likes_count: int = 0


class HighlightSavedResponse(BaseModel):
    """Состояние сохранения хайлайта после изменения.

    Attributes:
        highlight_id: Идентификатор хайлайта.
        saved: Итоговое состояние отметки «сохранён».
    """

    highlight_id: int
    saved: bool


class HighlightLikerResponse(BaseModel):
    """Пользователь, лайкнувший хайлайт.

    Attributes:
        user_id: Идентификатор пользователя.
        username: Отображаемое имя пользователя.
        created_at: Дата лайка в текстовом виде.
    """

    user_id: int
    username: str
    created_at: str


class HighlightLikersResponse(BaseModel):
    """Список пользователей, лайкнувших хайлайт.

    Attributes:
        items: Пользователи в порядке последних лайков.
    """

    items: list[HighlightLikerResponse]


class HighlightCommentResponse(BaseModel):
    """Комментарий к хайлайту.

    Attributes:
        id: Идентификатор комментария.
        user_id: Идентификатор автора.
        username: Отображаемое имя автора.
        content: Текст комментария.
        created_at: Дата комментария в текстовом виде.
    """

    id: int
    user_id: int
    username: str
    content: str
    created_at: str


class HighlightCommentsResponse(BaseModel):
    """Список комментариев хайлайта.

    Attributes:
        items: Комментарии в порядке добавления.
    """

    items: list[HighlightCommentResponse]
