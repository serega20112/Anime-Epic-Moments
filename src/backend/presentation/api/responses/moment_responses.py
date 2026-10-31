"""Модели ответов моментов просмотра."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class ViewingMomentResponse(BaseModel):
    """Черновик момента просмотра в JSON-представлении.

    Attributes:
        id: Идентификатор черновика.
        anime_id: Идентификатор аниме.
        episode: Номер серии.
        timestamp: Отметка момента в секундах.
        watch_source_id: Идентификатор источника воспроизведения.
        caption: Подпись к моменту.
        sticker: Идентификатор наклейки.
        screenshot_url: Ссылка на сохранённый кадр.
        created_at: Момент создания черновика.
    """

    id: int | None = None
    anime_id: int
    episode: int
    timestamp: float
    watch_source_id: int | None = None
    caption: str | None = None
    sticker: str | None = None
    screenshot_url: str | None = None
    created_at: datetime | None = None


class PublishMomentResponse(BaseModel):
    """Ответ на публикацию черновика как хайлайта.

    Attributes:
        highlight_id: Идентификатор созданного хайлайта.
    """

    highlight_id: int


class MomentDeletedResponse(BaseModel):
    """Подтверждение удаления черновика.

    Attributes:
        deleted: Признак успешного удаления.
    """

    deleted: bool
