from src.backend.infrastructure.cache.highlight_dashboard_cache import (
    HighlightDashboardCache,
)
from src.backend.infrastructure.external.anime_api_client import AnimeApiClient
from src.backend.infrastructure.repositories.user_repository import UserRepository
from src.backend.repository.highlight_repository import HighlightRepository
from src.backend.use_case.highlight.get_user_highlights import GetUserHighlightsUseCase


class GetPublicTopHighlightsUseCase(GetUserHighlightsUseCase):
    """Возвращает публичный топ хайлайтов в формате дашборда."""

    def __init__(
        self,
        repo: HighlightRepository,
        anime_api_client: AnimeApiClient,
        highlight_dashboard_cache: HighlightDashboardCache | None = None,
        user_repo: UserRepository | None = None,
    ):
        super().__init__(repo, anime_api_client, user_repo=user_repo)
        self.highlight_dashboard_cache = highlight_dashboard_cache

    async def execute(
        self,
        limit: int = 20,
        anime_id: int | None = None,
        emotion: str | None = None,
        category: str | None = None,
        sort_by: str = "popular",
        created_date: str | None = None,
        query: str | None = None,
        include_spoilers: bool = False,
        viewer_user_id: int | None = None,
    ):
        normalized_sort = sort_by if sort_by in {"popular", "recent"} else "popular"
        use_cache = self.highlight_dashboard_cache is not None and viewer_user_id is None
        if use_cache:
            cached = await self.highlight_dashboard_cache.get_public(
                limit=limit,
                anime_id=anime_id,
                emotion=emotion,
                category=category,
                sort_by=normalized_sort,
                created_date=created_date,
                query=query,
                include_spoilers=include_spoilers,
            )
            if cached is not None:
                return cached
        highlights = (
            await self.repo.get_public_top(limit)
            if normalized_sort == "popular"
            else await self.repo.get_public_recent(limit)
        )
        dashboard = await self._build_dashboard(
            highlights=highlights,
            anime_id=anime_id,
            emotion=emotion,
            category=category,
            sort_by=normalized_sort,
            created_date=created_date,
            query=query,
            include_spoilers=include_spoilers,
            viewer_user_id=viewer_user_id,
        )
        if use_cache:
            await self.highlight_dashboard_cache.set_public(
                limit=limit,
                anime_id=anime_id,
                emotion=emotion,
                category=category,
                sort_by=normalized_sort,
                created_date=created_date,
                query=query,
                include_spoilers=include_spoilers,
                value=dashboard,
            )
        return dashboard
