"""Модели запросов моментов просмотра."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class SaveViewingMomentRequest(BaseModel):
    """Тело запроса сохранения черновика момента.

    Клиент может прислать ``user_id``: поле игнорируется, потому что владелец
    берётся только из сессии.

    Attributes:
        episode: Номер серии, по умолчанию первая.
        timestamp: Отметка момента в секундах.
        watch_source_id: Идентификатор источника воспроизведения.
        caption: Подпись к моменту.
        sticker: Идентификатор наклейки.
        screenshot_url: Ссылка на сохранённый кадр.
        moment_id: Идентификатор обновляемого черновика, если он уже есть.
    """

    model_config = ConfigDict(extra="ignore")

    episode: int = Field(default=1, gt=0)
    timestamp: float = Field(default=0.0, ge=0)
    watch_source_id: int | None = None
    caption: str | None = None
    sticker: str | None = None
    screenshot_url: str | None = None
    moment_id: int | None = Field(default=None, gt=0)


class PublishViewingMomentRequest(BaseModel):
    """Тело запроса публикации черновика как хайлайта.

    Attributes:
        is_spoiler: Помечать ли хайлайт спойлером.
        title: Название хайлайта; при отсутствии берётся из черновика.
        category: Категория хайлайта; при отсутствии берётся из наклейки.
        emotion: Эмоция момента.
        description: Описание хайлайта.
    """

    model_config = ConfigDict(extra="ignore")

    is_spoiler: bool = False
    title: str | None = None
    category: str | None = None
    emotion: str | None = None
    description: str | None = None
