"""Модели ответов коллекций."""

from __future__ import annotations

from pydantic import BaseModel

from backend.presentation.api.responses.anime_responses import AnimeCardResponse


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


class MobileCollectionResponse(BaseModel):
    """Коллекция пользователя в мобильном представлении.

    Attributes:
        id: Идентификатор коллекции.
        title: Название коллекции.
        is_public: Открыта ли коллекция другим пользователям.
        item_count: Число аниме в коллекции.
        cover_url: Ссылка на обложку либо None.
        owner_id: Идентификатор владельца коллекции.
    """

    id: int
    title: str
    is_public: bool
    item_count: int
    cover_url: str | None = None
    owner_id: int


class MobileCollectionsResponse(BaseModel):
    """Список коллекций пользователя.

    Attributes:
        items: Коллекции владельца в порядке создания.
    """

    items: list[MobileCollectionResponse]


class MobileCollectionItemsResponse(BaseModel):
    """Элементы коллекции в мобильном представлении.

    Attributes:
        items: Карточки аниме коллекции.
    """

    items: list[AnimeCardResponse]


class CollectionItemAddedResponse(BaseModel):
    """Итог добавления аниме в коллекцию.

    Attributes:
        collection_id: Идентификатор коллекции.
        anime_id: Идентификатор добавленного аниме.
        added: Признак успешного добавления.
    """

    collection_id: int
    anime_id: int
    added: bool
