from dataclasses import dataclass

from src.backend.domain.user.value_object import FollowUserCard
from src.backend.infrastructure.external.anime_api_client import AnimeApiClient
from src.backend.infrastructure.repositories.user_repository import UserRepository
from src.backend.repository.highlight_repository import HighlightRepository
from src.backend.use_case.highlight.get_user_highlights import GetUserHighlightsUseCase


@dataclass
class FollowingHighlightsPage:
    dashboard: object
    followed_users: list[FollowUserCard]
    total_following: int


class GetFollowingHighlightsUseCase(GetUserHighlightsUseCase):
    """Собирает ленту хайлайтов пользователей, на которых подписан зритель."""

    def __init__(
        self,
        repo: HighlightRepository,
        anime_api_client: AnimeApiClient,
        user_repo: UserRepository,
    ):
        super().__init__(repo, anime_api_client, user_repo=user_repo)
        self.user_repo = user_repo

    def execute(
        self,
        follower_user_id: int,
        anime_id: int | None = None,
        emotion: str | None = None,
        category: str | None = None,
        sort_by: str = "recent",
        created_date: str | None = None,
        query: str | None = None,
        include_spoilers: bool = False,
        limit: int = 24,
    ) -> FollowingHighlightsPage:
        followed_users = self.user_repo.get_followed_users(follower_user_id, limit=12)
        followed_ids = [user.id for user in followed_users if user.id is not None]
        highlights = self.repo.get_by_users(followed_ids, limit=max(limit * 4, 48))
        dashboard = self._build_dashboard(
            highlights=highlights,
            anime_id=anime_id,
            emotion=emotion,
            category=category,
            sort_by=sort_by,
            created_date=created_date,
            query=query,
            include_spoilers=include_spoilers,
            viewer_user_id=follower_user_id,
        )
        dashboard.items = dashboard.items[:limit]
        dashboard.stats.total_highlights = len(dashboard.items)
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
            total_following=self.user_repo.get_follow_stats(follower_user_id)[1],
        )
