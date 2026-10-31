"""Команда удаления аниме из коллекции."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RemoveCollectionItemCommand:
    """Команда удаления аниме из коллекции.

    Attributes:
        collection_id: Идентификатор коллекции.
        anime_id: Идентификатор удаляемого аниме.
        user_id: Идентификатор пользователя; только он вправе менять состав.
    """

    collection_id: int
    anime_id: int
    user_id: int
