import json

from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from src.backend.infrastructure.repositories._async import repository_method
from src.backend.domain.collection.entity import AnimeCollection, AnimeCollectionItem
from src.backend.infrastructure.models.sqlalchemy_models import (
    AnimeCollectionItemModel,
    AnimeCollectionModel,
)


class CollectionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    @repository_method
    def create_collection(self, collection: AnimeCollection) -> AnimeCollection:
        row = AnimeCollectionModel(
            user_id=collection.user_id,
            title=collection.title,
            description=collection.description,
            is_public=collection.is_public,
        )
        self.session.add(row)
        self.session.commit()
        collection.id = row.id
        collection.created_at = row.created_at
        return collection

    @repository_method
    def get_by_id(self, collection_id: int) -> AnimeCollection | None:
        row = self.session.query(AnimeCollectionModel).filter_by(id=collection_id).first()
        if row is None:
            return None
        return AnimeCollection(
            id=row.id,
            user_id=row.user_id,
            title=row.title,
            description=row.description or "",
            is_public=row.is_public,
            created_at=row.created_at,
        )

    @repository_method
    def get_user_collections(self, user_id: int) -> list[AnimeCollection]:
        rows = (
            self.session.query(AnimeCollectionModel)
            .filter_by(user_id=user_id)
            .order_by(AnimeCollectionModel.created_at.desc())
            .all()
        )
        return [
            AnimeCollection(
                id=row.id,
                user_id=row.user_id,
                title=row.title,
                description=row.description or "",
                is_public=row.is_public,
                created_at=row.created_at,
            )
            for row in rows
        ]

    @repository_method
    def get_public_user_collections(self, user_id: int) -> list[AnimeCollection]:
        rows = (
            self.session.query(AnimeCollectionModel)
            .filter_by(user_id=user_id, is_public=True)
            .order_by(AnimeCollectionModel.created_at.desc())
            .all()
        )
        return [
            AnimeCollection(
                id=row.id,
                user_id=row.user_id,
                title=row.title,
                description=row.description or "",
                is_public=row.is_public,
                created_at=row.created_at,
            )
            for row in rows
        ]

    @repository_method
    def add_item(self, item: AnimeCollectionItem) -> AnimeCollectionItem:
        existing = (
            self.session.query(AnimeCollectionItemModel)
            .filter_by(collection_id=item.collection_id, anime_id=item.anime_id)
            .first()
        )
        if existing is not None:
            item.id = existing.id
            item.added_at = existing.added_at
            return item
        row = AnimeCollectionItemModel(
            collection_id=item.collection_id,
            anime_id=item.anime_id,
            title=item.title,
            description=item.description,
            cover_url=item.cover_url,
            genres_json=self._dump_genres(item.genres),
        )
        self.session.add(row)
        self.session.commit()
        item.id = row.id
        item.added_at = row.added_at
        return item

    @repository_method
    def remove_item(self, collection_id: int, anime_id: int) -> None:
        row = (
            self.session.query(AnimeCollectionItemModel)
            .filter_by(collection_id=collection_id, anime_id=anime_id)
            .first()
        )
        if row is not None:
            self.session.delete(row)
            self.session.commit()

    @repository_method
    def get_items(self, collection_id: int) -> list[AnimeCollectionItem]:
        rows = (
            self.session.query(AnimeCollectionItemModel)
            .filter_by(collection_id=collection_id)
            .order_by(AnimeCollectionItemModel.added_at.desc())
            .all()
        )
        return [
            AnimeCollectionItem(
                id=row.id,
                collection_id=row.collection_id,
                anime_id=row.anime_id,
                title=row.title,
                description=row.description or "",
                cover_url=row.cover_url,
                genres=self._load_genres(row.genres_json),
                added_at=row.added_at,
            )
            for row in rows
        ]

    @repository_method
    def get_items_count_map(self, collection_ids: list[int]) -> dict[int, int]:
        if not collection_ids:
            return {}
        rows = (
            self.session.query(
                AnimeCollectionItemModel.collection_id,
                func.count(AnimeCollectionItemModel.id),
            )
            .filter(AnimeCollectionItemModel.collection_id.in_(collection_ids))
            .group_by(AnimeCollectionItemModel.collection_id)
            .all()
        )
        return {int(collection_id): int(count) for collection_id, count in rows}

    def _dump_genres(self, genres: list[str] | None) -> str | None:
        if not genres:
            return None
        return json.dumps(genres, ensure_ascii=False)

    def _load_genres(self, payload: str | None) -> list[str]:
        if not payload:
            return []
        try:
            data = json.loads(payload)
        except (TypeError, ValueError):
            return []
        if not isinstance(data, list):
            return []
        return [str(item).strip() for item in data if str(item).strip()]
