from src.backend.domain.highlight.entity import Highlight
from src.backend.domain.highlight.policy import HighlightPolicy
from src.backend.infrastructure.cache.highlight_dashboard_cache import (
    HighlightDashboardCache,
)
from src.backend.infrastructure.cache.profile_overview_cache import ProfileOverviewCache
from src.backend.repository.highlight_repository import HighlightRepository
from src.backend.services.recommendation_service import RecommendationService


class CreateHighlightUseCase:
    """
    Use case для создания Highlight
    """

    def __init__(
        self,
        repo: HighlightRepository,
        recommendation_service: RecommendationService | None = None,
        highlight_dashboard_cache: HighlightDashboardCache | None = None,
        profile_overview_cache: ProfileOverviewCache | None = None,
    ):
        self.repo = repo
        self.recommendation_service = recommendation_service
        self.highlight_dashboard_cache = highlight_dashboard_cache
        self.profile_overview_cache = profile_overview_cache

    async def execute(
        self,
        user_id: int | None,
        anime_id: int,
        episode: int,
        start_timestamp: float,
        end_timestamp: float,
        title: str = "",
        category: str | None = None,
        description: str = "",
        is_spoiler: bool = False,
        emotion: str | None = None,
        highlights_this_hour: int = 0,
    ) -> Highlight:
        if not HighlightPolicy.can_add_highlight(user_id, highlights_this_hour):
            raise PermissionError("Превышен лимит добавления хайлайтов для гостя")

        if not HighlightPolicy.filter_spoiler_content(f"{title} {description}"):
            raise ValueError("Описание содержит запрещённый контент")

        highlight = Highlight(
            user_id=user_id,
            anime_id=anime_id,
            episode=episode,
            start_timestamp=start_timestamp,
            end_timestamp=end_timestamp,
            title=title or f"Момент {episode} серии",
            category=category,
            description=description,
            is_spoiler=is_spoiler,
            emotion=emotion,
        )

        result = await self.repo.add(highlight)
        if self.recommendation_service and user_id is not None:
            await self.recommendation_service.invalidate_user(int(user_id))
        if self.highlight_dashboard_cache is not None:
            await self.highlight_dashboard_cache.invalidate_public()
        if self.profile_overview_cache is not None and user_id is not None:
            await self.profile_overview_cache.invalidate_user(int(user_id), include_ai_summary=True)
        return result
