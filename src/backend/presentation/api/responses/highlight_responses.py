"""Модели ответов JSON-маршрутов хайлайтов."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from backend.presentation.api.responses.pagination import Page


class MobileHighlightCardResponse(BaseModel):
    """Карточка хайлайта в мобильной ленте.

    Отражает доменную карточку :class:`HighlightCard` и принимает её напрямую
    (``from_attributes``), поэтому маршрут не собирает словарь вручную.

    Attributes:
        id: Идентификатор хайлайта.
        anime_id: Идентификатор аниме во внешнем каталоге.
        anime_title: Название аниме.
        anime_cover: Обложка аниме либо None.
        title: Заголовок хайлайта.
        category: Категория либо None.
        episode: Номер серии.
        start_timestamp: Начало фрагмента в тексте ``MM:SS``.
        end_timestamp: Конец фрагмента в тексте ``MM:SS``.
        duration_seconds: Длительность фрагмента в секундах.
        description: Описание хайлайта.
        is_spoiler: Помечен ли хайлайт спойлером.
        emotion: Метка эмоции либо None.
        created_at: Дата создания в тексте ``YYYY-MM-DD``.
        likes_count: Число лайков.
        views_count: Число просмотров.
        comments_count: Число комментариев.
        is_liked: Лайкнул ли текущий зритель.
        is_saved: Сохранил ли текущий зритель.
        watch_url: Ссылка на просмотр с начала фрагмента.
        share_url: Публичная ссылка хайлайта.
        owner_user_id: Идентификатор автора либо None.
        owner_username: Имя автора либо None.
        owner_avatar_url: Аватар автора либо None.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    anime_id: int
    anime_title: str
    anime_cover: str | None = None
    title: str
    category: str | None = None
    episode: int
    start_timestamp: str
    end_timestamp: str
    duration_seconds: float
    description: str
    is_spoiler: bool
    emotion: str | None = None
    created_at: str
    likes_count: int
    views_count: int
    comments_count: int
    is_liked: bool
    is_saved: bool
    watch_url: str
    share_url: str
    owner_user_id: int | None = None
    owner_username: str | None = None
    owner_avatar_url: str | None = None


class HighlightFeedPageResponse(Page[MobileHighlightCardResponse]):
    """Страница мобильной ленты хайлайтов."""


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
