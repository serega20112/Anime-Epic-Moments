"""Сценарий общей ленты хайлайтов."""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence
from dataclasses import replace

from backend.application.dto import HighlightDashboardQuery, HighlightFeedQuery
from backend.application.interface.repositories.favorite_repository import FavoriteRepository
from backend.application.interface.repositories.highlight_repository import HighlightRepository
from backend.application.use_cases.highlight.feed.get_user_highlights import (
    GetUserHighlightsUseCase,
)
from backend.domain import (
    Highlight,
    HighlightAnimeGroup,
    HighlightCard,
    HighlightEngagement,
    HighlightFeedPage,
    User,
)


class GetHighlightFeedUseCase(GetUserHighlightsUseCase):
    """Собирает социальный фид хайлайтов с персональными секциями."""

    async def execute(self, query: HighlightFeedQuery) -> HighlightFeedPage:
        """Возвращает фид хайлайтов в формате feed-страницы.

        Args:
            query: Фильтры ленты и зритель для персональных секций.

        Returns:
            HighlightFeedPage: Страница фида с секциями.
        """
        dashboard_query = HighlightDashboardQuery(
            anime_id=query.anime_id,
            category=query.category,
            include_spoilers=query.include_spoilers,
            viewer_user_id=query.viewer_user_id,
        )
        async with self._unit_of_work as uow:
            repository = uow.repository(HighlightRepository)
            popular_source = await repository.get_public_top(query.limit)
            recent_source = await repository.get_public_recent(query.limit)
            liked_source: list[Highlight] = []
            favorite_source: list[Highlight] = []
            profile = None
            recent_activity: list = []
            if query.viewer_user_id is not None:
                liked_source = await repository.get_liked_by_user(
                    query.viewer_user_id, limit=query.limit
                )
                favorites = await uow.repository(FavoriteRepository).get_by_user(
                    query.viewer_user_id
                )
                favorite_source = await repository.get_from_anime_ids(
                    [favorite.anime_id for favorite in favorites], limit=query.limit
                )
                profile = await repository.get_profile_summary(query.viewer_user_id)
                recent_activity = await repository.get_recent_activity(query.viewer_user_id)
            sources = [popular_source, recent_source, liked_source, favorite_source]
            combined = [highlight for source in sources for highlight in source]
            engagement_map = await repository.get_engagement_map(
                [item.id for item in combined if item.id is not None],
                viewer_user_id=query.viewer_user_id,
            )
            owner_map = await self._load_owners(uow, combined)

        popular_query = replace(dashboard_query, sort_by="popular")
        recent_query = replace(dashboard_query, sort_by="recent")
        popular_items = await self._build_section(
            popular_source, popular_query, engagement_map, owner_map
        )
        recent_items = await self._build_section(
            recent_source, recent_query, engagement_map, owner_map
        )
        liked_items = await self._build_section(
            liked_source, popular_query, engagement_map, owner_map
        )
        from_favorites_items = await self._build_section(
            favorite_source, popular_query, engagement_map, owner_map
        )

        combined_items = popular_items + recent_items + liked_items + from_favorites_items
        anime_counter = Counter((item.anime_id, item.anime_title) for item in combined_items)
        anime_groups = [
            HighlightAnimeGroup(anime_id=value[0], anime_title=value[1], count=count)
            for value, count in anime_counter.most_common()
        ]

        return HighlightFeedPage(
            items=combined_items,
            popular_items=popular_items,
            recent_items=recent_items,
            liked_items=liked_items,
            from_favorites_items=from_favorites_items,
            anime_groups=anime_groups,
            categories=sorted({item.category for item in combined_items if item.category}),
            selected_anime_id=query.anime_id,
            selected_category=query.category,
            include_spoilers=query.include_spoilers,
            profile=profile,
            recent_activity=recent_activity,
        )

    async def _build_section(
        self,
        highlights: Sequence[Highlight],
        query: HighlightDashboardQuery,
        engagement_map: dict[int, HighlightEngagement],
        owner_map: dict[int, User],
    ) -> list[HighlightCard]:
        """Собрать карточки одной секции фида.

        Args:
            highlights: Исходные хайлайты секции.
            query: Фильтры и сортировка секции.
            engagement_map: Социальные метрики по идентификаторам хайлайтов.
            owner_map: Авторы хайлайтов по идентификатору пользователя.

        Returns:
            list[HighlightCard]: Карточки секции.
        """
        dashboard = await self._build_dashboard(highlights, query, engagement_map, owner_map)
        return dashboard.items
