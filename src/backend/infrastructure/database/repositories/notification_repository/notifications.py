"""Реализация репозитория уведомлений."""

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.domain import Notification
from backend.infrastructure.database.models import NotificationModel


class NotificationRepository:
    """Доступ к данным центра уведомлений."""

    def __init__(self, session: AsyncSession):
        """Сохранить сессию запроса, через которую работает репозиторий."""
        self.session = session

    async def add(self, notification: Notification) -> Notification:
        """Сохранить новое уведомление и вернуть его с присвоенным идентификатором."""
        record = NotificationModel(
            user_id=notification.user_id,
            actor_user_id=notification.actor_user_id,
            kind=notification.kind,
            text=notification.text,
            anime_id=notification.anime_id,
            highlight_id=notification.highlight_id,
            is_read=notification.is_read,
            created_at=notification.created_at,
        )
        self.session.add(record)
        await self.session.flush()
        notification.id = record.id
        return notification

    async def get_by_user(self, user_id: int, limit: int = 20) -> list[Notification]:
        """Вернуть уведомления получателя в порядке новых сначала."""
        result = await self.session.execute(
            select(NotificationModel)
            .where(NotificationModel.user_id == user_id)
            .order_by(NotificationModel.created_at.desc(), NotificationModel.id.desc())
            .limit(limit)
        )
        return [self._to_entity(record) for record in result.scalars().all()]

    async def count_unread(self, user_id: int) -> int:
        """Вернуть число непрочитанных уведомлений получателя."""
        result = await self.session.execute(
            select(func.count())
            .select_from(NotificationModel)
            .where(NotificationModel.user_id == user_id, NotificationModel.is_read.is_(False))
        )
        return int(result.scalar_one() or 0)

    async def mark_read(self, user_id: int, notification_id: int) -> int:
        """Пометить одно уведомление прочитанным и вернуть число изменений."""
        result = await self.session.execute(
            update(NotificationModel)
            .where(
                NotificationModel.id == notification_id,
                NotificationModel.user_id == user_id,
                NotificationModel.is_read.is_(False),
            )
            .values(is_read=True)
        )
        await self.session.flush()
        return int(result.rowcount or 0)

    async def mark_all_read(self, user_id: int) -> int:
        """Пометить все уведомления получателя прочитанными и вернуть число изменений."""
        result = await self.session.execute(
            update(NotificationModel)
            .where(NotificationModel.user_id == user_id, NotificationModel.is_read.is_(False))
            .values(is_read=True)
        )
        await self.session.flush()
        return int(result.rowcount or 0)

    @staticmethod
    def _to_entity(record: NotificationModel) -> Notification:
        """Превратить строку модели в доменное уведомление."""
        return Notification(
            id=record.id,
            user_id=record.user_id,
            actor_user_id=record.actor_user_id,
            kind=record.kind,
            text=record.text,
            anime_id=record.anime_id,
            highlight_id=record.highlight_id,
            is_read=record.is_read,
            created_at=record.created_at,
        )
