from backend.application.use_cases.highlight.get_user_highlights import GetUserHighlightsUseCase
from backend.domain import UserRepository
from backend.domain.repositories.highlight_repository import HighlightRepository
from backend.domain.services import AnimeApiClientInterface as AnimeApiClient


class GetSavedHighlightsUseCase(GetUserHighlightsUseCase):
    """Возвращает дашборд сохраненных пользователем хайлайтов."""

    def __init__(
            self,
            repo: HighlightRepository,
            anime_api_client: AnimeApiClient,
            user_repo: UserRepository | None = None,
    ):
        super().__init__(repo, anime_api_client, user_repo=user_repo)

    async def execute(
            self,
            user_id: int,
            anime_id: int | None = None,
            emotion: str | None = None,
            category: str | None = None,
            sort_by: str = "recent",
            created_date: str | None = None,
            query: str | None = None,
            include_spoilers: bool = True,
    ):
        highlights = await self.repo.get_saved_by_user(user_id)
        return await self._build_dashboard(
            highlights=highlights,
            anime_id=anime_id,
            emotion=emotion,
            category=category,
            sort_by=sort_by,
            created_date=created_date,
            query=query,
            include_spoilers=include_spoilers,
            viewer_user_id=user_id,
        )
