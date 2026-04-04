from src.backend.infrastructure.external.anime_api_client import AnimeApiClient
from src.backend.infrastructure.repositories.user_repository import UserRepository
from src.backend.repository.highlight_repository import HighlightRepository
from src.backend.use_case.highlight.get_user_highlights import GetUserHighlightsUseCase


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
        highlight = await self.repo.increment_views(highlight_id)
        return await self._build_dashboard(
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
