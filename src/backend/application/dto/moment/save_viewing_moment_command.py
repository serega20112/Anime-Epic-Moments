"""Создание и обновление черновика момента просмотра."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SaveViewingMomentCommand:
    """Команда сохранения черновика момента.

    Attributes:
        user_id: Идентификатор владельца черновика.
        anime_id: Идентификатор аниме.
        episode: Номер серии.
        timestamp: Отметка момента в секундах.
        watch_source_id: Идентификатор источника воспроизведения.
        caption: Подпись к моменту.
        sticker: Идентификатор наклейки.
        screenshot_url: Ссылка на сохранённый кадр.
        moment_id: Идентификатор обновляемого черновика, если он уже есть.
    """

    user_id: int
    anime_id: int
    episode: int
    timestamp: float = 0.0
    watch_source_id: int | None = None
    caption: str | None = None
    sticker: str | None = None
    screenshot_url: str | None = None
    moment_id: int | None = None
