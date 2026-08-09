from backend.application.use_cases.highlight.result import HighlightResult
from backend.application.use_cases.highlight.get_user_highlights import GetUserHighlightsUseCase
from backend.domain import UserRepository
from backend.domain.repositories.highlight_repository import HighlightRepository
from backend.domain.services import AnimeApiClientInterface as AnimeApiClient


class GetSharedHighlightUseCase(GetUserHighlightsUseCase):
    """Возвращает публичную карточку одного хайлайта и увеличивает счетчик просмотров."""

    def __init__(
            self,
            repo: HighlightRepository,
            anime_api_client: AnimeApiClient,
            user_repo: UserRepository | None = None,
    ):
        super().__init__(repo, anime_api_client, user_repo=user_repo)

    async def execute(self, highlight_id: int, viewer_user_id: int | None = None):
        highlight = await self.repo.get_by_id(highlight_id)
        if not highlight:
            return HighlightResult.failure("highlight_not_found", status_code=404)
        await self.repo.increment_views(highlight_id)
        dashboard = await self._build_dashboard(
            highlights=[highlight],
            anime_id=None,
            emotion=None,
            category=None,
            sort_by="recent",
            created_date=None,
            query=None,
            include_spoilers=True,
            viewer_user_id=viewer_user_id,
        )
        return HighlightResult.success(dashboard)
