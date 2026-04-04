from collections import Counter

from src.backend.domain.highlight.value_object import HighlightAnimeGroup, HighlightFeedPage
from src.backend.infrastructure.external.anime_api_client import AnimeApiClient
from src.backend.infrastructure.repositories.user_repository import UserRepository
from src.backend.repository.favorite_repository import FavoriteRepository
from src.backend.repository.highlight_repository import HighlightRepository
from src.backend.use_case.highlight.get_user_highlights import GetUserHighlightsUseCase


class GetHighlightFeedUseCase(GetUserHighlightsUseCase):
    """Собирает социальный фид хайлайтов с персональными секциями."""

    def __init__(
        self,
        repo: HighlightRepository,
        anime_api_client: AnimeApiClient,
        favorite_repo: FavoriteRepository,
        user_repo: UserRepository | None = None,
    ):
        super().__init__(repo, anime_api_client, user_repo=user_repo)
        self.favorite_repo = favorite_repo

    async def execute(
        self,
        viewer_user_id: int | None = None,
        anime_id: int | None = None,
        category: str | None = None,
        include_spoilers: bool = False,
        limit: int = 12,
    ) -> HighlightFeedPage:
        popular_items = (
            await self._build_dashboard(
            highlights=await self.repo.get_public_top(limit),
            anime_id=anime_id,
            emotion=None,
            category=category,
            sort_by="popular",
            created_date=None,
            query=None,
            include_spoilers=include_spoilers,
            viewer_user_id=viewer_user_id,
        )).items
        recent_items = (
            await self._build_dashboard(
            highlights=await self.repo.get_public_recent(limit),
            anime_id=anime_id,
            emotion=None,
            category=category,
            sort_by="recent",
            created_date=None,
            query=None,
            include_spoilers=include_spoilers,
            viewer_user_id=viewer_user_id,
        )).items

        liked_items = []
        from_favorites_items = []
        profile = None
        recent_activity = []
        if viewer_user_id is not None:
            liked_items = (
                await self._build_dashboard(
                highlights=await self.repo.get_liked_by_user(viewer_user_id, limit=limit),
                anime_id=anime_id,
                emotion=None,
                category=category,
                sort_by="popular",
                created_date=None,
                query=None,
                include_spoilers=include_spoilers,
                viewer_user_id=viewer_user_id,
            )).items
            favorite_anime_ids = [
                favorite.anime_id for favorite in await self.favorite_repo.get_by_user(viewer_user_id)
            ]
            from_favorites_items = (
                await self._build_dashboard(
                highlights=await self.repo.get_from_anime_ids(favorite_anime_ids, limit=limit),
                anime_id=anime_id,
                emotion=None,
                category=category,
                sort_by="popular",
                created_date=None,
                query=None,
                include_spoilers=include_spoilers,
                viewer_user_id=viewer_user_id,
            )).items
            profile = await self.repo.get_profile_summary(viewer_user_id)
            recent_activity = await self.repo.get_recent_activity(viewer_user_id)

        combined_items = popular_items + recent_items + liked_items + from_favorites_items
        anime_counter = Counter((item.anime_id, item.anime_title) for item in combined_items)
        anime_groups = [
            HighlightAnimeGroup(anime_id=value[0], anime_title=value[1], count=count)
            for value, count in anime_counter.most_common()
        ]
        categories = sorted({item.category for item in combined_items if item.category})

        return HighlightFeedPage(
            popular_items=popular_items,
            recent_items=recent_items,
            liked_items=liked_items,
            from_favorites_items=from_favorites_items,
            anime_groups=anime_groups,
            categories=categories,
            selected_anime_id=anime_id,
            selected_category=category,
            include_spoilers=include_spoilers,
            profile=profile,
            recent_activity=recent_activity,
        )
