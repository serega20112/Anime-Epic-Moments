"""Схемы тел запросов маршрутов хайлайтов."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

TITLE_MAX_LENGTH = 120
DESCRIPTION_MAX_LENGTH = 600
CATEGORY_MAX_LENGTH = 60
EMOTION_MAX_LENGTH = 40


class CreateHighlightRequest(BaseModel):
    """Тело создания хайлайта из плеера или формы.

    Attributes:
        anime_id: Идентификатор аниме.
        episode: Номер серии.
        start_timestamp: Начало фрагмента в секундах.
        end_timestamp: Конец фрагмента в секундах.
        title: Заголовок хайлайта.
        category: Категория хайлайта.
        description: Описание хайлайта.
        is_spoiler: Помечен ли хайлайт как спойлер.
        emotion: Эмоция, выбранная автором.
    """

    model_config = ConfigDict(extra="ignore")

    anime_id: int = Field(gt=0)
    episode: int = Field(gt=0)
    start_timestamp: float = Field(ge=0)
    end_timestamp: float = Field(ge=0)
    title: str = Field(default="", max_length=TITLE_MAX_LENGTH)
    category: str | None = Field(default=None, max_length=CATEGORY_MAX_LENGTH)
    description: str = Field(default="", max_length=DESCRIPTION_MAX_LENGTH)
    is_spoiler: bool = False
    emotion: str | None = Field(default=None, max_length=EMOTION_MAX_LENGTH)


class EditHighlightRequest(BaseModel):
    """Тело правки существующего хайлайта.

    Attributes:
        episode: Номер серии; без значения остаётся прежний.
        start_timestamp: Начало фрагмента в секундах.
        end_timestamp: Конец фрагмента в секундах.
        title: Заголовок хайлайта.
        category: Категория хайлайта.
        description: Описание хайлайта.
        is_spoiler: Помечен ли хайлайт как спойлер.
        emotion: Эмоция, выбранная автором.
    """

    model_config = ConfigDict(extra="ignore")

    episode: int | None = Field(default=None, gt=0)
    start_timestamp: float = Field(ge=0)
    end_timestamp: float = Field(ge=0)
    title: str = Field(default="", max_length=TITLE_MAX_LENGTH)
    category: str | None = Field(default=None, max_length=CATEGORY_MAX_LENGTH)
    description: str = Field(default="", max_length=DESCRIPTION_MAX_LENGTH)
    is_spoiler: bool = False
    emotion: str | None = Field(default=None, max_length=EMOTION_MAX_LENGTH)


class AddHighlightCommentRequest(BaseModel):
    """Тело добавления комментария к хайлайту.

    Attributes:
        content: Текст комментария.
    """

    model_config = ConfigDict(extra="ignore")

    content: str = Field(min_length=1, max_length=DESCRIPTION_MAX_LENGTH)
