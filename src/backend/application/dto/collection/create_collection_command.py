"""Создание коллекции аниме."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CreateCollectionCommand:
    """Команда создания коллекции.

    Attributes:
        user_id: Идентификатор владельца коллекции.
        title: Название коллекции.
        description: Описание коллекции.
        is_public: Доступна ли коллекция другим пользователям.
        cover_url: Ссылка на обложку коллекции.
    """

    user_id: int
    title: str
    description: str = ""
    is_public: bool = True
    cover_url: str | None = None
