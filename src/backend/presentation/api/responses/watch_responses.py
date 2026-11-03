"""Модели ответов JSON-маршрутов просмотра."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from backend.presentation.api.responses.anime_responses import AnimeCardResponse
from backend.presentation.api.responses.pagination import Page


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


class ProgressSavedResponse(BaseModel):
    """Ответ мобильного сохранения позиции просмотра.

    Attributes:
        saved: Итог записи позиции.
        watched: Пересечён ли серверный порог «просмотрено» для серии.
    """

    saved: bool
    watched: bool = False


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


class LibraryEntryResponse(BaseModel):
    """Карточка тайтла из дневника пользователя в JSON-представлении.

    Attributes:
        anime: Карточка тайтла из каталога.
        status: Статус просмотра в дневнике.
        current_episode: Текущая серия прогресса либо None.
        rating: Оценка пользователя либо None.
        last_watched_at: Дата последнего просмотра либо None.
    """

    model_config = ConfigDict(from_attributes=True)

    anime: AnimeCardResponse
    status: str
    current_episode: int | None = None
    rating: float | None = None
    last_watched_at: str | None = None


class HistoryEntryResponse(BaseModel):
    """Карточка тайтла из истории просмотров в JSON-представлении.

    Attributes:
        anime: Карточка тайтла из каталога.
        episode: Номер серии последней сессии.
        position_seconds: Сохранённая позиция в серии.
        watched_at: Дата сессии в текстовом виде.
    """

    model_config = ConfigDict(from_attributes=True)

    anime: AnimeCardResponse
    episode: int
    position_seconds: float
    watched_at: str


class LibraryPageResponse(Page[LibraryEntryResponse]):
    """Страница библиотеки просмотра пользователя."""


class HistoryPageResponse(Page[HistoryEntryResponse]):
    """Страница истории просмотров пользователя."""


class EpisodeProgressResponse(BaseModel):
    """Прогресс по одной серии тайтла для мобильного клиента.

    Attributes:
        number: Номер серии.
        title: Название серии либо None, когда каталог его не отдаёт.
        duration_seconds: Длительность серии либо None, когда неизвестна.
        watched: Просмотрена ли серия по позиции дневника зрителя.
        position_seconds: Позиция продолжения просмотра.
    """

    model_config = ConfigDict(from_attributes=True)

    number: int
    title: str | None = None
    duration_seconds: int | None = None
    watched: bool = False
    position_seconds: float = 0.0


class SourceResponse(BaseModel):
    """Источник просмотра серии для мобильного плеера.

    Attributes:
        episode_number: Номер серии источника.
        translation: Название озвучки или саба.
        quality: Метка качества.
        source_type: Тип источника (stream, embed, external).
        url: Адрес потока или файла воспроизведения.
    """

    episode_number: int
    translation: str
    quality: str
    source_type: str
    url: str


class AnimeDetailResponse(BaseModel):
    """Карточка тайтла с сериями, источниками и состояниями зрителя.

    Attributes:
        anime: Карточка тайтла из каталога.
        episode: Текущая серия запроса.
        episode_total: Общее число серий либо None.
        episodes: Прогресс по доступным сериям.
        sources: Источники текущей серии в порядке приоритета.
        favorites: В избранном ли тайтл у зрителя.
        user_rating: Оценка зрителя либо None.
        watch_status: Статус просмотра в дневнике либо None.
        last_position_seconds: Позиция продолжения текущей серии.
    """

    anime: AnimeCardResponse
    episode: int
    episode_total: int | None = None
    episodes: list[EpisodeProgressResponse] = []
    sources: list[SourceResponse] = []
    favorites: bool = False
    user_rating: int | None = None
    watch_status: str | None = None
    last_position_seconds: float = 0.0
