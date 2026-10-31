"""Переводы и playable-источники: справочник того, где смотреть.

`TranslationModel` описывает логический вариант озвучки/перевода, `WatchSourceModel` —
конкретную ссылку от провайдера. Записи идемпотентны: повторная синхронизация того же
источника не плодит дублей, а подписанные короткие ссылки удаляются перед вставкой
свежих, иначе плеер отдаёт протухшую ссылку.
"""

from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.domain import Translation, WatchSource
from backend.infrastructure.database.models import TranslationModel, WatchSourceModel


class WatchSourceRepositoryMixin:
    """Доступ к переводам и источникам просмотра."""

    session: AsyncSession

    async def get_translations(self, anime_id: int) -> list[Translation]:
        """Вернуть переводы аниме.

        Args:
            anime_id: Идентификатор аниме.

        Returns:
            list[Translation]: Подходящие переводы, отсортированные по названию.
        """
        result = await self.session.execute(
            select(TranslationModel)
            .where(TranslationModel.anime_id == anime_id)
            .order_by(TranslationModel.name.asc())
        )
        return [
            Translation(
                id=row.id,
                anime_id=row.anime_id,
                name=row.name,
                translation_type=row.translation_type,
                language=row.language,
                created_at=row.created_at,
            )
            for row in result.scalars().all()
        ]

    async def add_translation(self, translation: Translation) -> Translation:
        """Создать перевод, если такого же ещё нет.

        Args:
            translation: Агрегат перевода для сохранения.

        Returns:
            Translation: Существующий либо новый перевод.
        """
        result = await self.session.execute(
            select(TranslationModel).where(
                TranslationModel.anime_id == translation.anime_id,
                TranslationModel.name == translation.name,
                TranslationModel.translation_type == translation.translation_type,
                TranslationModel.language == translation.language,
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            translation.id = existing.id
            translation.created_at = existing.created_at
            return translation

        row = TranslationModel(
            anime_id=translation.anime_id,
            name=translation.name,
            translation_type=translation.translation_type,
            language=translation.language,
        )
        self.session.add(row)
        await self.session.flush()
        translation.id = row.id
        translation.created_at = row.created_at
        return translation

    async def get_sources(
        self,
        anime_id: int,
        episode: int | None = None,
    ) -> list[WatchSource]:
        """Вернуть источники просмотра аниме.

        Args:
            anime_id: Идентификатор аниме.
            episode: Необязательный фильтр по серии.

        Returns:
            list[WatchSource]: Подходящие источники.
        """
        stmt = select(WatchSourceModel).where(WatchSourceModel.anime_id == anime_id)
        if episode is not None:
            stmt = stmt.where(WatchSourceModel.episode == episode)
        stmt = stmt.order_by(WatchSourceModel.episode.asc(), WatchSourceModel.quality_label.desc())
        result = await self.session.execute(stmt)
        return [
            WatchSource(
                id=row.id,
                anime_id=row.anime_id,
                episode=row.episode,
                translation_id=row.translation_id,
                provider_name=row.provider_name,
                source_name=row.source_name,
                stream_url=row.stream_url,
                quality_label=row.quality_label,
                source_type=row.source_type or "stream",
                created_at=row.created_at,
            )
            for row in result.scalars().all()
        ]

    async def add_source(self, source: WatchSource) -> WatchSource:
        """Создать источник, если идентичный уже сохранён — вернуть существующий.

        Args:
            source: Агрегат источника для сохранения.

        Returns:
            WatchSource: Существующий либо новый источник.
        """
        result = await self.session.execute(
            select(WatchSourceModel).where(
                WatchSourceModel.anime_id == source.anime_id,
                WatchSourceModel.episode == source.episode,
                WatchSourceModel.translation_id == source.translation_id,
                WatchSourceModel.provider_name == source.provider_name,
                WatchSourceModel.source_name == source.source_name,
                WatchSourceModel.stream_url == source.stream_url,
                WatchSourceModel.quality_label == source.quality_label,
                WatchSourceModel.source_type == source.source_type,
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            source.id = existing.id
            source.created_at = existing.created_at
            return source

        row = WatchSourceModel(
            anime_id=source.anime_id,
            episode=source.episode,
            translation_id=source.translation_id,
            provider_name=source.provider_name,
            source_name=source.source_name,
            stream_url=source.stream_url,
            quality_label=source.quality_label,
            source_type=source.source_type,
        )
        self.session.add(row)
        await self.session.flush()
        source.id = row.id
        source.created_at = row.created_at
        return source

    async def delete_sources_by_provider(
        self,
        anime_id: int,
        provider_name: str,
        episode: int | None = None,
    ) -> None:
        """Удалить источники провайдера перед вставкой свежих ссылок.

        Нужно провайдерам с подписанными короткоживущими URL: устаревшие строки
        иначе обслуживались бы вечно, потому что синхронизация пропускает провайдеров,
        у которых уже есть сохранённые источники.

        Args:
            anime_id: Идентификатор аниме.
            provider_name: Провайдер, чьи источники удаляются.
            episode: Необязательный фильтр по серии.
        """
        stmt = delete(WatchSourceModel).where(
            WatchSourceModel.anime_id == anime_id,
            WatchSourceModel.provider_name == provider_name,
        )
        if episode is not None:
            stmt = stmt.where(WatchSourceModel.episode == episode)
        await self.session.execute(stmt)
