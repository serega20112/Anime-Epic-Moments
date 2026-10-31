"""Аналитика просмотров: статистика по тайтлам и дневная активность.

Обе выборки читаются только для витрины профиля и агрегируются в базе, чтобы не
тасовать тысячи строк сессий в процесс приложения.
"""

from __future__ import annotations

from datetime import timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.domain.clock import utc_now
from backend.domain.value_objects.watch.page_data import ViewingHeatmapPoint, WatchedAnimeStat
from backend.infrastructure.database.models import ViewingSessionModel


class WatchAnalyticsRepositoryMixin:
    """Агрегаты просмотра для статистики профиля."""

    session: AsyncSession

    async def get_watched_anime_stats(
        self,
        user_id: int,
        limit: int | None = None,
    ) -> list[WatchedAnimeStat]:
        """Посчитать статистику просмотра по каждому аниме пользователя.

        Args:
            user_id: Идентификатор пользователя.
            limit: Максимальное число результатов.

        Returns:
            list[WatchedAnimeStat]: Статистика, упорядоченная по намотанным секундам.
        """
        watched_seconds_expr = func.sum(ViewingSessionModel.position_seconds).label(
            "watched_seconds"
        )
        stmt = (
            select(
                ViewingSessionModel.anime_id,
                watched_seconds_expr,
                func.count(ViewingSessionModel.id).label("sessions_count"),
                func.max(ViewingSessionModel.updated_at).label("last_watched_at"),
            )
            .where(ViewingSessionModel.user_id == user_id)
            .group_by(ViewingSessionModel.anime_id)
            .order_by(
                watched_seconds_expr.desc(),
                func.max(ViewingSessionModel.updated_at).desc(),
            )
        )
        if limit is not None:
            stmt = stmt.limit(limit)
        result = await self.session.execute(stmt)
        rows = result.all()
        return [
            WatchedAnimeStat(
                anime_id=int(row.anime_id),
                watched_seconds=float(row.watched_seconds or 0.0),
                sessions_count=int(row.sessions_count or 0),
                last_watched_at=(
                    row.last_watched_at.strftime("%Y-%m-%d") if row.last_watched_at else ""
                ),
            )
            for row in rows
        ]

    async def get_viewing_heatmap(
        self,
        user_id: int,
        days: int = 35,
    ) -> list[ViewingHeatmapPoint]:
        """Считать дневную активность просмотров за последние `days` дней.

        Дни без просмотров возвращаются с нулём: витрине профиля нужен непрерывный ряд
        фиксированной длины. Без заполнения «35 дней» дают столько столбцов, сколько дней
        было активно, из-за чего масштаб высоты столбцов и подпись над ними теряют смысл.

        Args:
            user_id: Идентификатор пользователя.
            days: Количество дней в окне, включая сегодняшний.

        Returns:
            list[ViewingHeatmapPoint]: Ровно `days` точек от самого старого дня к сегоднянему.
        """
        window_days = max(int(days), 1)
        since = utc_now() - timedelta(days=window_days - 1)
        activity_date_expr = func.date(ViewingSessionModel.updated_at).label("activity_date")
        stmt = (
            select(
                activity_date_expr,
                func.count(ViewingSessionModel.id).label("interactions"),
            )
            .where(
                ViewingSessionModel.user_id == user_id,
                ViewingSessionModel.updated_at >= since,
            )
            .group_by(activity_date_expr)
            .order_by(activity_date_expr.asc())
        )
        result = await self.session.execute(stmt)
        counts_by_date = {
            str(row.activity_date): int(row.interactions or 0) for row in result.all()
        }

        today = utc_now().date()
        points = [
            ViewingHeatmapPoint(
                date=day.isoformat(),
                interactions=counts_by_date.get(day.isoformat(), 0),
            )
            for day in (today - timedelta(days=offset) for offset in range(window_days))
        ]
        return list(reversed(points))
