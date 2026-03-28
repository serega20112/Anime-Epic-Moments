from src.backend.domain.user.value_object import ProfileOverview
from src.backend.infrastructure.external.anime_api_client import AnimeApiClient
from src.backend.repository.highlight_repository import HighlightRepository
from src.backend.repository.user_repository import UserRepository
from src.backend.use_case.highlight.get_liked_highlights import GetLikedHighlightsUseCase
from src.backend.use_case.highlight.get_saved_highlights import GetSavedHighlightsUseCase
from src.backend.use_case.highlight.get_user_highlights import GetUserHighlightsUseCase


class GetProfileOverviewUseCase:
    """Собирает профиль пользователя с social-статистикой и быстрыми подборками."""

    def __init__(
        self,
        user_repo: UserRepository,
        highlight_repo: HighlightRepository,
        anime_api_client: AnimeApiClient,
    ):
        self.user_repo = user_repo
        self.highlight_repo = highlight_repo
        self.recent_highlights_use_case = GetUserHighlightsUseCase(
            highlight_repo,
            anime_api_client,
        )
        self.liked_highlights_use_case = GetLikedHighlightsUseCase(
            highlight_repo,
            anime_api_client,
        )
        self.saved_highlights_use_case = GetSavedHighlightsUseCase(
            highlight_repo,
            anime_api_client,
        )

    def execute(self, user_id: int) -> ProfileOverview:
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError("Пользователь не найден")

        recent_dashboard = self.recent_highlights_use_case.execute(
            user_id=user_id,
            include_spoilers=True,
            viewer_user_id=user_id,
            sort_by="recent",
        )
        popular_dashboard = self.recent_highlights_use_case.execute(
            user_id=user_id,
            include_spoilers=True,
            viewer_user_id=user_id,
            sort_by="popular",
        )
        liked_dashboard = self.liked_highlights_use_case.execute(
            user_id=user_id,
            include_spoilers=True,
            sort_by="popular",
        )
        saved_dashboard = self.saved_highlights_use_case.execute(
            user_id=user_id,
            include_spoilers=True,
            sort_by="popular",
        )

        return ProfileOverview(
            user_id=user.id or user_id,
            email=user.email,
            username=user.username,
            avatar_url=user.avatar_url,
            created_at=user.created_at.strftime("%Y-%m-%d"),
            summary=self.highlight_repo.get_profile_summary(user_id),
            recent_highlights=recent_dashboard.items[:4],
            popular_highlights=popular_dashboard.items[:4],
            liked_highlights=liked_dashboard.items[:4],
            saved_highlights=saved_dashboard.items[:4],
            recent_activity=self.highlight_repo.get_recent_activity(user_id, limit=8),
        )
