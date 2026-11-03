"""Схемы тел запросов маршрутов просмотра."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

TITLE_MAX_LENGTH = 120
DESCRIPTION_MAX_LENGTH = 600
CATEGORY_MAX_LENGTH = 60
EMOTION_MAX_LENGTH = 40
QUALITY_MAX_LENGTH = 40
STATUS_MAX_LENGTH = 40
TRANSLATION_MAX_LENGTH = 80
TRANSLATION_TYPE_MAX_LENGTH = 40
PROVIDER_MAX_LENGTH = 60
LANGUAGE_MAX_LENGTH = 20
SOURCE_TYPE_MAX_LENGTH = 20
STREAM_URL_MAX_LENGTH = 2048
DEFAULT_LANGUAGE = "ru"
DEFAULT_SOURCE_TYPE = "stream"
DEFAULT_TRANSLATION_TYPE = "dub"


class UpdateWatchStatusRequest(BaseModel):
    """Тело обновления статуса просмотра аниме.

    Attributes:
        status: Новый статус просмотра.
    """

    model_config = ConfigDict(extra="ignore")

    status: str = Field(default="", max_length=STATUS_MAX_LENGTH)


class SaveViewingSessionRequest(BaseModel):
    """Тело сохранения состояния плеера.

    Attributes:
        episode: Номер серии.
        watch_source_id: Идентификатор источника воспроизведения.
        position_seconds: Текущая позиция в секундах.
        volume: Уровень громкости.
        quality_label: Выбранное качество.
        is_paused: Приостановлено ли воспроизведение.
    """

    model_config = ConfigDict(extra="ignore")

    episode: int | None = Field(default=None, ge=1)
    watch_source_id: int | None = Field(default=None, ge=1)
    position_seconds: float = Field(default=0.0, ge=0)
    volume: float = Field(default=1.0, ge=0, le=1)
    quality_label: str = Field(default="Auto", max_length=QUALITY_MAX_LENGTH)
    is_paused: bool = False


class SaveProgressRequest(BaseModel):
    """Тело сохранения позиции просмотра мобильным плеером.

    Повторяет состояние веб-плеера и добавляет длительность серии: по позиции
    и длительности сервер сам решает, пересечён ли порог «просмотрено».

    Attributes:
        episode: Номер серии.
        watch_source_id: Идентификатор источника воспроизведения.
        position_seconds: Текущая позиция в секундах.
        duration_seconds: Длительность серии либо None, если клиенту неизвестна.
        volume: Уровень громкости.
        quality_label: Выбранное качество.
        is_paused: Приостановлено ли воспроизведение.
    """

    model_config = ConfigDict(extra="ignore")

    episode: int | None = Field(default=None, ge=1)
    watch_source_id: int | None = Field(default=None, ge=1)
    position_seconds: float = Field(default=0.0, ge=0)
    duration_seconds: float | None = Field(default=None, ge=0)
    volume: float = Field(default=1.0, ge=0, le=1)
    quality_label: str = Field(default="Auto", max_length=QUALITY_MAX_LENGTH)
    is_paused: bool = False


class CompleteEpisodeRequest(BaseModel):
    """Тело отметки просмотренной серии.

    Attributes:
        episode: Номер просмотренной серии.
    """

    model_config = ConfigDict(extra="ignore")

    episode: int | None = Field(default=None, ge=1)


class CreateWatchHighlightRequest(BaseModel):
    """Тело создания хайлайта из плеера.

    Attributes:
        episode: Номер серии.
        title: Заголовок хайлайта.
        category: Категория хайлайта.
        start_timestamp: Начало фрагмента в секундах.
        end_timestamp: Конец фрагмента в секундах.
        description: Описание хайлайта.
        is_spoiler: Помечен ли хайлайт как спойлер.
        emotion: Эмоция, выбранная автором.
        watch_source_id: Идентификатор источника воспроизведения.
        translation_id: Идентификатор озвучки.
        original_title: Оригинальное название аниме.
    """

    model_config = ConfigDict(extra="ignore")

    episode: int | None = Field(default=None, ge=1)
    title: str = Field(default="", max_length=TITLE_MAX_LENGTH)
    category: str | None = Field(default=None, max_length=CATEGORY_MAX_LENGTH)
    start_timestamp: float | None = Field(default=None, ge=0)
    end_timestamp: float | None = Field(default=None, ge=0)
    description: str = Field(default="", max_length=DESCRIPTION_MAX_LENGTH)
    is_spoiler: bool = False
    emotion: str | None = Field(default=None, max_length=EMOTION_MAX_LENGTH)
    watch_source_id: int | None = Field(default=None, ge=1)
    translation_id: int | None = Field(default=None, ge=1)
    original_title: str | None = Field(default=None, max_length=TITLE_MAX_LENGTH)


class AddAnimeCommentRequest(BaseModel):
    """Тело комментария в обсуждение аниме.

    Attributes:
        content: Текст комментария.
    """

    model_config = ConfigDict(extra="ignore")

    content: str = Field(default="", max_length=DESCRIPTION_MAX_LENGTH)


class DiscoverSourcesRequest(BaseModel):
    """Тело поиска источников просмотра у провайдера.

    Attributes:
        episode: Номер серии; без значения берётся первая серия.
    """

    model_config = ConfigDict(extra="ignore")

    episode: int | None = Field(default=None, ge=1)


class AddWatchSourceRequest(BaseModel):
    """Тело ручного добавления источника просмотра.

    Attributes:
        episode: Номер серии.
        translation_name: Название озвучки.
        translation_type: Тип озвучки.
        provider_name: Название внешнего провайдера.
        source_name: Название источника внутри провайдера.
        stream_url: Адрес потока.
        quality_label: Метка качества.
        language: Язык озвучки.
        source_type: Технический тип источника.
    """

    model_config = ConfigDict(extra="ignore")

    episode: int = Field(ge=1)
    translation_name: str = Field(min_length=1, max_length=TRANSLATION_MAX_LENGTH)
    translation_type: str = Field(
        default=DEFAULT_TRANSLATION_TYPE, max_length=TRANSLATION_TYPE_MAX_LENGTH
    )
    provider_name: str = Field(min_length=1, max_length=PROVIDER_MAX_LENGTH)
    source_name: str = Field(min_length=1, max_length=TITLE_MAX_LENGTH)
    stream_url: str = Field(min_length=8, max_length=STREAM_URL_MAX_LENGTH)
    quality_label: str = Field(default="Auto", max_length=QUALITY_MAX_LENGTH)
    language: str = Field(default=DEFAULT_LANGUAGE, max_length=LANGUAGE_MAX_LENGTH)
    source_type: str = Field(default=DEFAULT_SOURCE_TYPE, max_length=SOURCE_TYPE_MAX_LENGTH)
