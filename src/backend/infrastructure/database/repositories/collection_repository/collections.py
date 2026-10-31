"""Реализация репозитория: класс пакета и сборка mixin'ов по агрегатам."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.domain.aggregates.collection.collection import AnimeCollection
from backend.domain.entities.collection.collection_item import AnimeCollectionItem
from backend.infrastructure.database.models import (
    AnimeCollectionItemModel,
    AnimeCollectionModel,
)
from backend.infrastructure.database.serialization import dump_genres, load_genres


class CollectionRepository:
    """Доступ к данным коллекций аниме."""

    def __init__(self, session: AsyncSession):
        """Сохранить сессию запроса, через которую работает репозиторий."""
        self.session = session

    async def create_collection(self, collection: AnimeCollection) -> AnimeCollection:
        """Сохранить новую коллекцию."""
        row = AnimeCollectionModel(
            user_id=collection.user_id,
            title=collection.title,
            description=collection.description,
            is_public=collection.is_public,
            cover_url=collection.cover_url,
        )
        self.session.add(row)
        await self.session.flush()
        collection.id = row.id
        collection.created_at = row.created_at
        return collection

    async def get_by_id(self, collection_id: int) -> AnimeCollection | None:
        """Загрузить коллекцию по идентификатору."""
        result = await self.session.execute(
            select(AnimeCollectionModel).where(AnimeCollectionModel.id == collection_id)
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None
        return await self._to_collection(row)

    async def get_user_collections(self, user_id: int) -> list[AnimeCollection]:
        """Вернуть все коллекции пользователя."""
        result = await self.session.execute(
            select(AnimeCollectionModel)
            .where(AnimeCollectionModel.user_id == user_id)
            .order_by(AnimeCollectionModel.created_at.desc())
        )
        return [await self._to_collection(row) for row in result.scalars().all()]

    async def get_public_user_collections(self, user_id: int) -> list[AnimeCollection]:
        """Вернуть публичные коллекции пользователя."""
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
        """Добавить аниме в коллекцию, пропуская повторы."""
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
            genres_json=dump_genres(item.genres),
            original_title=item.original_title,
        )
        self.session.add(row)
        await self.session.flush()
        item.id = row.id
        item.added_at = row.added_at
        return item

    async def remove_item(self, collection_id: int, anime_id: int) -> None:
        """Удалить аниме из коллекции."""
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
        """Вернуть элементы коллекции."""
        result = await self.session.execute(
            select(AnimeCollectionItemModel)
            .where(AnimeCollectionItemModel.collection_id == collection_id)
            .order_by(AnimeCollectionItemModel.added_at.desc())
        )
        return [await self._to_item(row) for row in result.scalars().all()]

    async def get_items_count_map(self, collection_ids: list[int]) -> dict[int, int]:
        """Вернуть число элементов для каждой коллекции."""
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
            cover_url=row.cover_url,
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
            genres=load_genres(row.genres_json),
            added_at=row.added_at,
            original_title=row.original_title,
        )
