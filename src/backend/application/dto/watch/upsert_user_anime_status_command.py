"""Создание и обновление статуса просмотра аниме."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class UpsertUserAnimeStatusCommand:
    """Команда сохранения статуса просмотра.

    Attributes:
        user_id: Идентификатор действующего пользователя.
        anime_id: Идентификатор аниме.
        status: Статус просмотра.
        current_episode: Текущая серия.
        rating: Оценка пользователя.
        note: Заметка к статусу.
        started_at: Дата начала просмотра.
        completed_at: Дата завершения просмотра.
    """

    user_id: int
    anime_id: int
    status: str
    current_episode: int | None = None
    rating: float | None = None
    note: str | None = None
    started_at: str | None = None
    completed_at: str | None = None
