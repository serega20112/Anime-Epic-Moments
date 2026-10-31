"""Карточки коллекций для интерфейса."""

from dataclasses import dataclass


@dataclass(frozen=True)
class CollectionCard:
    """Краткая карточка коллекции со счётчиком элементов."""

    id: int
    title: str
    description: str
    items_count: int
    is_public: bool
    created_at: str
    share_url: str
    cover_url: str | None = None


@dataclass(frozen=True)
class CollectionItemCard:
    """Карточка аниме внутри коллекции."""

    anime_id: int
    title: str
    description: str
    cover_url: str | None
    genres: list[str]
    watch_url: str
    original_title: str | None = None


@dataclass(frozen=True)
class CollectionDetails:
    """Коллекция вместе с её элементами и владельцем."""

    collection: CollectionCard
    items: list[CollectionItemCard]
