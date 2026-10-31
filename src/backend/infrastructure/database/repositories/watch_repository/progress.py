"""Прогресс просмотра: дневник пользователя по тайтлам.

Методы mixins работают с `UserAnimeStatusModel` — единственной таблицей, где живёт
статус («смотрю», «отложено», «посмотрено»), текущая серия и отметки времени.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.domain import UserAnimeStatus
from backend.domain.clock import utc_now
from backend.infrastructure.database.models import UserAnimeStatusModel


class WatchProgressRepositoryMixin:
    """Доступ к статусам просмотра пользователя."""

    session: AsyncSession

    async def get_status(self, user_id: int, anime_id: int) -> UserAnimeStatus | None:
        """Вернуть статус аниме у пользователя.

        Args:
            user_id: Идентификатор пользователя.
            anime_id: Идентификатор аниме.

        Returns:
            UserAnimeStatus | None: Статус либо None, если записи нет.
        """
        result = await self.session.execute(
            select(UserAnimeStatusModel).where(
                UserAnimeStatusModel.user_id == user_id,
                UserAnimeStatusModel.anime_id == anime_id,
            )
        )
        row = result.scalar_one_or_none()
        if not row:
            return None
        return await self._map_status(row)

    async def get_statuses_by_user(self, user_id: int) -> list[UserAnimeStatus]:
        """Вернуть все записи дневника пользователя.

        Args:
            user_id: Идентификатор пользователя.

        Returns:
            list[UserAnimeStatus]: Записи, отсортированные по времени обновления.
        """
        result = await self.session.execute(
            select(UserAnimeStatusModel)
            .where(UserAnimeStatusModel.user_id == user_id)
            .order_by(UserAnimeStatusModel.updated_at.desc(), UserAnimeStatusModel.id.desc())
        )
        return [await self._map_status(row) for row in result.scalars().all()]

    async def upsert_status(self, status: UserAnimeStatus) -> UserAnimeStatus:
        """Создать или обновить статус аниме.

        Args:
            status: Агрегат статуса для сохранения.

        Returns:
            UserAnimeStatus: Сохранённый статус.
        """
        result = await self.session.execute(
            select(UserAnimeStatusModel).where(
                UserAnimeStatusModel.user_id == status.user_id,
                UserAnimeStatusModel.anime_id == status.anime_id,
            )
        )
        row = result.scalar_one_or_none()
        if row:
            row.status = status.status
            row.current_episode = status.current_episode
            row.started_at = status.started_at
            row.completed_at = status.completed_at
            row.last_watched_at = status.last_watched_at
            row.rating = status.rating
            row.note = status.note
            row.updated_at = utc_now()
            await self.session.flush()
            status.id = row.id
            status.updated_at = row.updated_at
            return status

        row = UserAnimeStatusModel(
            user_id=status.user_id,
            anime_id=status.anime_id,
            status=status.status,
            current_episode=status.current_episode,
            started_at=status.started_at,
            completed_at=status.completed_at,
            last_watched_at=status.last_watched_at,
            rating=status.rating,
            note=status.note,
        )
        self.session.add(row)
        await self.session.flush()
        status.id = row.id
        status.updated_at = row.updated_at
        return status

    async def record_episode_completion(
        self,
        user_id: int,
        anime_id: int,
        episode: int,
    ) -> UserAnimeStatus:
        """Сдвинуть прогресс после досмотренной серии.

        Текущий статус сохраняется (по умолчанию «смотрю»), а `current_episode`
        поднимается до наибольшей увиденной серии: обратный ход не откатывает
        прогресс, чтобы досмотренные серии питали статистику и рекомендации.

        Args:
            user_id: Идентификатор пользователя.
            anime_id: Идентификатор аниме.
            episode: Номер завершённой серии.

        Returns:
            UserAnimeStatus: Обновлённая запись статуса.
        """
        result = await self.session.execute(
            select(UserAnimeStatusModel).where(
                UserAnimeStatusModel.user_id == user_id,
                UserAnimeStatusModel.anime_id == anime_id,
            )
        )
        row = result.scalar_one_or_none()
        now = utc_now()

        if row:
            if row.status in (None, ""):
                row.status = "watching"
            if row.current_episode is None or episode > row.current_episode:
                row.current_episode = episode
            row.last_watched_at = now
            row.updated_at = now
            await self.session.flush()
        else:
            row = UserAnimeStatusModel(
                user_id=user_id,
                anime_id=anime_id,
                status="watching",
                current_episode=episode,
                last_watched_at=now,
                updated_at=now,
            )
            self.session.add(row)
            await self.session.flush()

        return await self._map_status(row)

    @staticmethod
    async def _map_status(row: UserAnimeStatusModel) -> UserAnimeStatus:
        """Преобразовать строку статуса в доменную сущность.

        Args:
            row: ORM-строка статуса.

        Returns:
            UserAnimeStatus: Доменная сущность.
        """
        return UserAnimeStatus(
            id=row.id,
            user_id=row.user_id,
            anime_id=row.anime_id,
            status=row.status,
            updated_at=row.updated_at,
            current_episode=row.current_episode,
            started_at=row.started_at,
            completed_at=row.completed_at,
            last_watched_at=row.last_watched_at,
            rating=row.rating,
            note=row.note,
        )
