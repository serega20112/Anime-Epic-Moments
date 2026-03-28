from src.backend.infrastructure.external.anime_api_client import AnimeApiClient
from src.backend.infrastructure.cache.highlight_dashboard_cache import (
    HighlightDashboardCache,
)
from src.backend.repository.highlight_repository import HighlightRepository
from src.backend.use_case.highlight.get_user_highlights import GetUserHighlightsUseCase


class GetPublicTopHighlightsUseCase(GetUserHighlightsUseCase):
    """Возвращает публичный топ хайлайтов в формате дашборда."""

    def __init__(
        self,
        repo: HighlightRepository,
        anime_api_client: AnimeApiClient,
        highlight_dashboard_cache: HighlightDashboardCache | None = None,
    ):
        super().__init__(repo, anime_api_client)
        self.highlight_dashboard_cache = highlight_dashboard_cache

    def execute(
        self,
        limit: int = 20,
        anime_id: int | None = None,
        emotion: str | None = None,
        created_date: str | None = None,
        query: str | None = None,
        include_spoilers: bool = False,
    ):
        """Принимает лимит и фильтры, возвращает публичный дашборд хайлайтов."""
        if self.highlight_dashboard_cache is not None:
            cached = self.highlight_dashboard_cache.get_public(
                limit=limit,
                anime_id=anime_id,
                emotion=emotion,
                created_date=created_date,
                query=query,
                include_spoilers=include_spoilers,
            )
            if cached is not None:
                return cached
        highlights = self.repo.get_public_top(limit)
        dashboard = self._build_dashboard(
            highlights=highlights,
            anime_id=anime_id,
            emotion=emotion,
            created_date=created_date,
            query=query,
            include_spoilers=include_spoilers,
        )
        if self.highlight_dashboard_cache is not None:
            self.highlight_dashboard_cache.set_public(
                limit=limit,
                anime_id=anime_id,
                emotion=emotion,
                created_date=created_date,
                query=query,
                include_spoilers=include_spoilers,
                value=dashboard,
            )
        return dashboard
