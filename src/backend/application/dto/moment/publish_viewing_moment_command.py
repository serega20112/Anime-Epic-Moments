"""Публикация черновика момента просмотра как хайлайта."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PublishViewingMomentCommand:
    """Команда публикации черновика момента.

    Attributes:
        user_id: Идентификатор владельца черновика.
        moment_id: Идентификатор публикуемого момента.
        is_spoiler: Помечен ли хайлайт как спойлер.
        title: Заголовок публикуемого хайлайта.
        category: Категория хайлайта.
        emotion: Эмоция, выбранная автором.
        description: Описание хайлайта.
    """

    user_id: int
    moment_id: int
    is_spoiler: bool = False
    title: str | None = None
    category: str | None = None
    emotion: str | None = None
    description: str | None = None
