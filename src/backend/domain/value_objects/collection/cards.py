from dataclasses import dataclass


@dataclass
class CollectionCard:
    id: int
    title: str
    description: str
    items_count: int
    is_public: bool
    created_at: str
    share_url: str
    cover_url: str | None = None


@dataclass
class CollectionItemCard:
    anime_id: int
    title: str
    description: str
    cover_url: str | None
    genres: list[str]
    watch_url: str
    original_title: str | None = None


@dataclass
class CollectionDetails:
    collection: CollectionCard
    items: list[CollectionItemCard]
