"""Сценарий ленты хайлайтов подписок."""

from __future__ import annotations

from dataclasses import dataclass, replace

from backend.application.dto import HighlightDashboardQuery
from backend.application.interface.repositories.highlight_repository import HighlightRepository
from backend.application.interface.repositories.user_repository import UserRepository
from backend.application.use_cases.highlight.feed.get_user_highlights import (
    GetUserHighlightsUseCase,
)
from backend.domain import FollowUserCard, HighlightDashboard


@dataclass
class FollowingHighlightsPage:
    """Лента хайлайтов пользователей, на которых подписан зритель.

    Attributes:
        dashboard: Готовая страница дашборда с карточками.
        followed_users: Пользователи, чьи хайлайты попали в ленту.
        total_following: Сколько всего подписок у зрителя.
    """

    dashboard: HighlightDashboard
    followed_users: list[FollowUserCard]
    total_following: int


class GetFollowingHighlightsUseCase(GetUserHighlightsUseCase):
    """Собирает ленту хайлайтов пользователей, на которых подписан зритель."""

    async def execute(self, query: HighlightDashboardQuery) -> FollowingHighlightsPage:
        """Собрать ленту хайлайтов подписок.

        Args:
            query: Фильтры ленты; ``user_id`` — это зритель, чьи подписки читаются.

        Returns:
            FollowingHighlightsPage: Дашборд ленты и превью авторов.
        """
        follower_user_id = query.user_id if query.user_id is not None else query.viewer_user_id
        if follower_user_id is None:
            dashboard = await self._build_dashboard([], query, {}, {})
            return FollowingHighlightsPage(
                dashboard=dashboard,
                followed_users=[],
                total_following=0,
            )

        async with self._unit_of_work as uow:
            user_repository = uow.repository(UserRepository)
            followed_users = await user_repository.get_followed_users(follower_user_id, limit=12)
            followed_ids = [user.id for user in followed_users if user.id is not None]
            repository = uow.repository(HighlightRepository)
            highlights = await repository.get_by_users(followed_ids, limit=max(query.limit * 4, 48))
            engagement_map = await repository.get_engagement_map(
                [item.id for item in highlights if item.id is not None],
                viewer_user_id=follower_user_id,
            )
            owner_map = await self._load_owners(uow, highlights)
            follow_stats = await user_repository.get_follow_stats(follower_user_id)

        dashboard = await self._build_dashboard(
            highlights,
            replace(query, viewer_user_id=follower_user_id),
            engagement_map,
            owner_map,
        )
        truncated_items = dashboard.items[: query.limit]
        dashboard = replace(
            dashboard,
            items=truncated_items,
            stats=replace(dashboard.stats, total_highlights=len(truncated_items)),
        )
        return FollowingHighlightsPage(
            dashboard=dashboard,
            followed_users=[
                FollowUserCard(
                    user_id=user.id or 0,
                    username=user.username,
                    avatar_url=user.avatar_url,
                    profile_url=f"/users/{user.id}",
                )
                for user in followed_users
                if user.id is not None
            ],
            total_following=follow_stats[1],
        )
