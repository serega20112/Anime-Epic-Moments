"""Сессии плеера и playback-контексты хайлайтов.

`ViewingSessionModel` хранит позицию воспроизведения, громкость и качество — то, что
нужно для «продолжить с места остановки». `HighlightContextModel` закрепляет за
хайлайтом источник и перевод, чтобы момент открывался в том же контексте.
"""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.domain import HighlightContext, ViewingSession
from backend.domain.clock import utc_now
from backend.infrastructure.database.models import HighlightContextModel, ViewingSessionModel


class ViewingSessionRepositoryMixin:
    """Доступ к сессиям просмотра и контекстам хайлайтов."""

    session: AsyncSession

    async def get_session(
        self,
        user_id: int,
        anime_id: int,
        episode: int,
    ) -> ViewingSession | None:
        """Вернуть сессию просмотра серии у пользователя.

        Args:
            user_id: Идентификатор пользователя.
            anime_id: Идентификатор аниме.
            episode: Номер серии.

        Returns:
            ViewingSession | None: Сессия либо None, если её ещё нет.
        """
        result = await self.session.execute(
            select(ViewingSessionModel).where(
                ViewingSessionModel.user_id == user_id,
                ViewingSessionModel.anime_id == anime_id,
                ViewingSessionModel.episode == episode,
            )
        )
        row = result.scalar_one_or_none()
        if not row:
            return None
        return ViewingSession(
            id=row.id,
            user_id=row.user_id,
            anime_id=row.anime_id,
            episode=row.episode,
            watch_source_id=row.watch_source_id,
            position_seconds=row.position_seconds,
            volume=row.volume,
            quality_label=row.quality_label,
            is_paused=row.is_paused,
            updated_at=row.updated_at,
        )

    async def upsert_session(self, session: ViewingSession) -> ViewingSession:
        """Создать или обновить сессию просмотра.

        Args:
            session: Агрегат сессии для сохранения.

        Returns:
            ViewingSession: Сохранённая сессия.
        """
        result = await self.session.execute(
            select(ViewingSessionModel).where(
                ViewingSessionModel.user_id == session.user_id,
                ViewingSessionModel.anime_id == session.anime_id,
                ViewingSessionModel.episode == session.episode,
            )
        )
        row = result.scalar_one_or_none()
        if row:
            row.watch_source_id = session.watch_source_id
            row.position_seconds = session.position_seconds
            row.volume = session.volume
            row.quality_label = session.quality_label
            row.is_paused = session.is_paused
            row.updated_at = utc_now()
            await self.session.flush()
            session.id = row.id
            session.updated_at = row.updated_at
            return session

        row = ViewingSessionModel(
            user_id=session.user_id,
            anime_id=session.anime_id,
            episode=session.episode,
            watch_source_id=session.watch_source_id,
            position_seconds=session.position_seconds,
            volume=session.volume,
            quality_label=session.quality_label,
            is_paused=session.is_paused,
        )
        self.session.add(row)
        await self.session.flush()
        session.id = row.id
        session.updated_at = row.updated_at
        return session

    async def add_highlight_context(self, context: HighlightContext) -> HighlightContext:
        """Сохранить playback-контекст хайлайта.

        Args:
            context: Агрегат контекста для сохранения.

        Returns:
            HighlightContext: Сохранённый контекст.
        """
        row = HighlightContextModel(
            highlight_id=context.highlight_id,
            watch_source_id=context.watch_source_id,
            translation_id=context.translation_id,
            title=context.title,
            original_title=context.original_title,
        )
        self.session.add(row)
        await self.session.flush()
        context.id = row.id
        context.created_at = row.created_at
        return context

    async def get_highlight_contexts(self, highlight_ids: list[int]) -> list[HighlightContext]:
        """Вернуть контексты по списку идентификаторов хайлайтов.

        Args:
            highlight_ids: Идентификаторы хайлайтов.

        Returns:
            list[HighlightContext]: Подходящие контексты; пустой список на пустом входе.
        """
        if not highlight_ids:
            return []
        result = await self.session.execute(
            select(HighlightContextModel).where(
                HighlightContextModel.highlight_id.in_(highlight_ids)
            )
        )
        return [
            HighlightContext(
                id=row.id,
                highlight_id=row.highlight_id,
                watch_source_id=row.watch_source_id,
                translation_id=row.translation_id,
                title=row.title,
                created_at=row.created_at,
                original_title=row.original_title,
            )
            for row in result.scalars().all()
        ]

    async def get_recent_viewing_sessions(
        self,
        user_id: int,
        limit: int = 10,
    ) -> list[ViewingSession]:
        """Вернуть последние по времени сессии пользователя.

        Перезаписи одной и той же серии схлопываются в одну запись: берётся самая
        свежая строка на пару (anime_id, episode), иначе «недавно смотренное»
        превратилось бы в простыню из повторов.

        Args:
            user_id: Идентификатор пользователя.
            limit: Максимальное число сессий.

        Returns:
            list[ViewingSession]: Сессии, упорядоченные по времени обновления.
        """
        rank_expr = (
            func.row_number()
            .over(
                partition_by=(
                    ViewingSessionModel.anime_id,
                    ViewingSessionModel.episode,
                ),
                order_by=(
                    ViewingSessionModel.updated_at.desc(),
                    ViewingSessionModel.id.desc(),
                ),
            )
            .label("position_rank")
        )
        top_ids_result = await self.session.execute(
            select(
                ViewingSessionModel.id,
                rank_expr,
            )
            .where(ViewingSessionModel.user_id == user_id)
            .order_by(
                ViewingSessionModel.updated_at.desc(),
                ViewingSessionModel.id.desc(),
            )
            .limit(max(int(limit), 1) * 4)
        )
        top_ids = [int(row.id) for row in top_ids_result.all() if int(row.position_rank) == 1][
            : max(int(limit), 1)
        ]
        if not top_ids:
            return []
        result = await self.session.execute(
            select(ViewingSessionModel)
            .where(ViewingSessionModel.id.in_(top_ids))
            .order_by(
                ViewingSessionModel.updated_at.desc(),
                ViewingSessionModel.id.desc(),
            )
        )
        return [await self._map_session(row) for row in result.scalars().all()]

    @staticmethod
    async def _map_session(row: ViewingSessionModel) -> ViewingSession:
        """Преобразовать строку сессии в доменную сущность.

        Args:
            row: ORM-строка сессии просмотра.

        Returns:
            ViewingSession: Доменная сущность.
        """
        return ViewingSession(
            id=row.id,
            user_id=row.user_id,
            anime_id=row.anime_id,
            episode=row.episode,
            watch_source_id=row.watch_source_id,
            position_seconds=row.position_seconds,
            volume=row.volume,
            quality_label=row.quality_label,
            is_paused=row.is_paused,
            updated_at=row.updated_at,
        )
