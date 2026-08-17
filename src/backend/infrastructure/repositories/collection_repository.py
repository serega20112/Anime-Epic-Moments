import json

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.domain.collection.entity import AnimeCollection, AnimeCollectionItem
from backend.infrastructure.models import (
    AnimeCollectionItemModel,
    AnimeCollectionModel,
)


class CollectionRepository:
    """Data access for anime collections."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_collection(self, collection: AnimeCollection) -> AnimeCollection:
        """Persist a new collection.

        Args:
            collection: Collection aggregate to persist.

        Returns:
            AnimeCollection: The persisted collection.
        """
        row = AnimeCollectionModel(
            user_id=collection.user_id,
            title=collection.title,
            description=collection.description,
            is_public=collection.is_public,
        )
        self.session.add(row)
        await self.session.flush()
        collection.id = row.id
        collection.created_at = row.created_at
        return collection

    async def get_by_id(self, collection_id: int) -> AnimeCollection | None:
        """Fetch a collection by identifier.

        Args:
            collection_id: Collection identifier.

        Returns:
            AnimeCollection | None: The collection or None.
        """
        result = await self.session.execute(
            select(AnimeCollectionModel).where(AnimeCollectionModel.id == collection_id)
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None
        return await self._to_collection(row)

    async def get_user_collections(self, user_id: int) -> list[AnimeCollection]:
        """Return all collections of a user.

        Args:
            user_id: User identifier.

        Returns:
            list[AnimeCollection]: User collections.
        """
        result = await self.session.execute(
            select(AnimeCollectionModel)
            .where(AnimeCollectionModel.user_id == user_id)
            .order_by(AnimeCollectionModel.created_at.desc())
        )
        return [await self._to_collection(row) for row in result.scalars().all()]

    async def get_public_user_collections(self, user_id: int) -> list[AnimeCollection]:
        """Return public collections of a user.

        Args:
            user_id: User identifier.

        Returns:
            list[AnimeCollection]: Public user collections.
        """
        result = await self.session.execute(
            select(AnimeCollectionModel)
            .where(
                AnimeCollectionModel.user_id == user_id,
                AnimeCollectionModel.is_public.is_(True),
            )
            .order_by(AnimeCollectionModel.created_at.desc())
        )
        return [await self._to_collection(row) for row in result.scalars().all()]

    async def add_item(self, item: AnimeCollectionItem) -> AnimeCollectionItem:
        """Add an item to a collection, skipping duplicates.

        Args:
            item: Collection item to persist.

        Returns:
            AnimeCollectionItem: The persisted item.
        """
        result = await self.session.execute(
            select(AnimeCollectionItemModel).where(
                AnimeCollectionItemModel.collection_id == item.collection_id,
                AnimeCollectionItemModel.anime_id == item.anime_id,
            )
        )
        existing = result.scalar_one_or_none()
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
            genres_json=await self._dump_genres(item.genres),
        )
        self.session.add(row)
        await self.session.flush()
        item.id = row.id
        item.added_at = row.added_at
        return item

    async def remove_item(self, collection_id: int, anime_id: int) -> None:
        """Remove an item from a collection.

        Args:
            collection_id: Collection identifier.
            anime_id: Anime identifier.
        """
        result = await self.session.execute(
            select(AnimeCollectionItemModel).where(
                AnimeCollectionItemModel.collection_id == collection_id,
                AnimeCollectionItemModel.anime_id == anime_id,
            )
        )
        row = result.scalar_one_or_none()
        if row is not None:
            await self.session.delete(row)
            await self.session.flush()

    async def get_items(self, collection_id: int) -> list[AnimeCollectionItem]:
        """Return items of a collection.

        Args:
            collection_id: Collection identifier.

        Returns:
            list[AnimeCollectionItem]: Collection items.
        """
        result = await self.session.execute(
            select(AnimeCollectionItemModel)
            .where(AnimeCollectionItemModel.collection_id == collection_id)
            .order_by(AnimeCollectionItemModel.added_at.desc())
        )
        return [await self._to_item(row) for row in result.scalars().all()]

    async def get_items_count_map(self, collection_ids: list[int]) -> dict[int, int]:
        """Return item counts per collection.

        Args:
            collection_ids: Collection identifiers.

        Returns:
            dict[int, int]: Collection id to item count.
        """
        if not collection_ids:
            return {}
        result = await self.session.execute(
            select(
                AnimeCollectionItemModel.collection_id,
                func.count(AnimeCollectionItemModel.id),
            )
            .where(AnimeCollectionItemModel.collection_id.in_(collection_ids))
            .group_by(AnimeCollectionItemModel.collection_id)
        )
        return {int(collection_id): int(count) for collection_id, count in result.all()}

    async def _to_collection(self, row: AnimeCollectionModel) -> AnimeCollection:
        return AnimeCollection(
            id=row.id,
            user_id=row.user_id,
            title=row.title,
            description=row.description or "",
            is_public=row.is_public,
            created_at=row.created_at,
        )

    async def _to_item(self, row: AnimeCollectionItemModel) -> AnimeCollectionItem:
        return AnimeCollectionItem(
            id=row.id,
            collection_id=row.collection_id,
            anime_id=row.anime_id,
            title=row.title,
            description=row.description or "",
            cover_url=row.cover_url,
            genres=await self._load_genres(row.genres_json),
            added_at=row.added_at,
        )

    async def _dump_genres(self, genres: list[str] | None) -> str | None:
        if not genres:
            return None
        return json.dumps(genres, ensure_ascii=False)

    async def _load_genres(self, payload: str | None) -> list[str]:
        if not payload:
            return []
        try:
            data = json.loads(payload)
        except (TypeError, ValueError):
            return []
        if not isinstance(data, list):
            return []
        return [str(item).strip() for item in data if str(item).strip()]
