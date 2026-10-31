"""Модели ответов JSON-маршрутов просмотра."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class WatchStatusResponse(BaseModel):
    """Ответ на обновление статуса просмотра.

    Attributes:
        status: Записанный статус просмотра.
    """

    status: str


class WatchSessionResponse(BaseModel):
    """Ответ на сохранение сессии просмотра.

    Attributes:
        session_id: Идентификатор сохранённой сессии.
    """

    session_id: int | None = None


class EpisodeCompletionResponse(BaseModel):
    """Ответ на отметку просмотренной серии.

    Attributes:
        current_episode: Текущая серия прогресса.
        status: Текущий статус просмотра.
    """

    current_episode: int | None = None
    status: str | None = None


class WatchHighlightResponse(BaseModel):
    """Ответ на создание хайлайта из плеера.

    Attributes:
        highlight_id: Идентификатор созданного хайлайта.
    """

    highlight_id: int | None = None


class DiscoverSourcesResponse(BaseModel):
    """Ответ на поиск источников у внешнего провайдера.

    Attributes:
        enabled: Включён ли хотя бы один провайдер источников.
        sources_count: Число найденных источников.
        provider_names: Названия подключённых провайдеров.
    """

    enabled: bool
    sources_count: int
    provider_names: list[str]


class WatchSourceResponse(BaseModel):
    """Ответ на ручное добавление источника просмотра.

    Attributes:
        source_id: Идентификатор созданного источника.
        translation_id: Идентификатор созданной или найденной озвучки.
    """

    source_id: int | None = None
    translation_id: int | None = None


class AnimeCommentResponse(BaseModel):
    """Комментарий обсуждения аниме в JSON-представлении.

    Attributes:
        id: Идентификатор комментария.
        anime_id: Идентификатор аниме.
        user_id: Идентификатор автора.
        username: Отображаемое имя автора.
        content: Текст комментария.
        likes_count: Число лайков комментария.
        created_at: Дата комментария в текстовом виде.
        is_liked: Лайкнул ли комментарий текущий зритель.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    anime_id: int
    user_id: int
    username: str
    content: str
    likes_count: int
    created_at: str
    is_liked: bool = False
