from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.domain.moment.entity import ViewingMoment
from backend.infrastructure.models import ViewingMomentModel


class MomentRepository:
    """Data access for viewing moments."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def save_moment(self, moment: ViewingMoment) -> ViewingMoment:
        """Create or update a viewing moment.

        Args:
            moment: Moment aggregate to persist.

        Returns:
            ViewingMoment: The persisted moment.
        """
        if moment.id is not None:
            result = await self.session.execute(
                select(ViewingMomentModel).where(
                    ViewingMomentModel.id == moment.id,
                    ViewingMomentModel.user_id == moment.user_id,
                )
            )
            row = result.scalar_one_or_none()
            if row is not None:
                row.anime_id = moment.anime_id
                row.episode = moment.episode
                row.timestamp = moment.timestamp
                row.watch_source_id = moment.watch_source_id
                row.caption = moment.caption
                row.sticker = moment.sticker
                row.screenshot_url = moment.screenshot_url
                await self.session.flush()
                moment.created_at = row.created_at
                return moment

        row = ViewingMomentModel(
            user_id=moment.user_id,
            anime_id=moment.anime_id,
            episode=moment.episode,
            timestamp=moment.timestamp,
            watch_source_id=moment.watch_source_id,
            caption=moment.caption,
            sticker=moment.sticker,
            screenshot_url=moment.screenshot_url,
        )
        self.session.add(row)
        await self.session.flush()
        moment.id = row.id
        moment.created_at = row.created_at
        return moment

    async def get_moment(self, moment_id: int, user_id: int) -> ViewingMoment | None:
        """Fetch a moment owned by the user.

        Args:
            moment_id: Moment identifier.
            user_id: Owner identifier.

        Returns:
            ViewingMoment | None: The moment or None when missing.
        """
        result = await self.session.execute(
            select(ViewingMomentModel).where(
                ViewingMomentModel.id == moment_id,
                ViewingMomentModel.user_id == user_id,
            )
        )
        row = result.scalar_one_or_none()
        if not row:
            return None
        return ViewingMoment(
            id=row.id,
            user_id=row.user_id,
            anime_id=row.anime_id,
            episode=row.episode,
            timestamp=row.timestamp,
            watch_source_id=row.watch_source_id,
            caption=row.caption,
            sticker=row.sticker,
            screenshot_url=row.screenshot_url,
            created_at=row.created_at,
        )

    async def get_moments_by_user(self, user_id: int) -> list[ViewingMoment]:
        """Fetch all draft moments of a user.

        Args:
            user_id: Owner identifier.

        Returns:
            list[ViewingMoment]: Moments ordered by creation time.
        """
        result = await self.session.execute(
            select(ViewingMomentModel)
            .where(ViewingMomentModel.user_id == user_id)
            .order_by(ViewingMomentModel.created_at.desc(), ViewingMomentModel.id.desc())
        )
        return [
            ViewingMoment(
                id=row.id,
                user_id=row.user_id,
                anime_id=row.anime_id,
                episode=row.episode,
                timestamp=row.timestamp,
                watch_source_id=row.watch_source_id,
                caption=row.caption,
                sticker=row.sticker,
                screenshot_url=row.screenshot_url,
                created_at=row.created_at,
            )
            for row in result.scalars().all()
        ]

    async def delete_moment(self, moment_id: int, user_id: int) -> bool:
        """Delete a moment owned by the user.

        Args:
            moment_id: Moment identifier.
            user_id: Owner identifier.

        Returns:
            bool: True when a moment was deleted.
        """
        result = await self.session.execute(
            delete(ViewingMomentModel).where(
                ViewingMomentModel.id == moment_id,
                ViewingMomentModel.user_id == user_id,
            )
        )
        await self.session.flush()
        return result.rowcount > 0
