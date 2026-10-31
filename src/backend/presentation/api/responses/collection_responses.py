"""Модели ответов коллекций."""

from __future__ import annotations

from pydantic import BaseModel


class CollectionSummaryResponse(BaseModel):
    """Краткая карточка коллекции для выбора в интерфейсе.

    Attributes:
        id: Идентификатор коллекции.
        title: Название коллекции.
    """

    id: int
    title: str


class MyCollectionsResponse(BaseModel):
    """Ответ со списком коллекций пользователя.

    Attributes:
        collections: Краткие карточки коллекций.
    """

    collections: list[CollectionSummaryResponse]
