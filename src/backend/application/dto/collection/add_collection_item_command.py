"""Добавление аниме в существующую коллекцию."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class AddCollectionItemCommand:
    """Команда добавления аниме в коллекцию.

    Attributes:
        collection_id: Идентификатор коллекции.
        anime_id: Идентификатор добавляемого аниме.
        user_id: Идентификатор действующего пользователя для проверки владения.
        title: Название аниме для снимка карточки.
        description: Описание аниме для снимка карточки.
        cover_url: Ссылка на обложку для снимка карточки.
        genres: Жанры аниме для снимка карточки.
        original_title: Оригинальное название аниме.
    """

    collection_id: int
    anime_id: int
    user_id: int
    title: str = ""
    description: str = ""
    cover_url: str | None = None
    genres: list[str] = field(default_factory=list)
    original_title: str | None = None
