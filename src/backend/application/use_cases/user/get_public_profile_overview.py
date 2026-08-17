from backend.application.use_cases.auth.get_profile_overview import GetProfileOverviewUseCase
from backend.application.use_cases.user.result import UserResult
from backend.domain import (
    FollowUserCard,
    PublicProfileOverview,
    UserRepository,
)
from backend.domain.collection.value_object import CollectionCard
from backend.domain.repositories.collection_repository import CollectionRepository


class GetPublicProfileOverviewUseCase:
    """Собирает публичный профиль пользователя с коллекциями и social-статистикой."""

    def __init__(
        self,
        profile_overview_use_case: GetProfileOverviewUseCase,
        user_repo: UserRepository,
        collection_repo: CollectionRepository,
    ):
        self.profile_overview_use_case = profile_overview_use_case
        self.user_repo = user_repo
        self.collection_repo = collection_repo

    async def execute(
        self,
        profile_user_id: int,
        viewer_user_id: int | None = None,
    ) -> UserResult:
        try:
            profile = await self.profile_overview_use_case.execute(profile_user_id)
        except ValueError:
            return await UserResult.failure("Пользователь не найден", status_code=404)
        followers_count, following_count = await self.user_repo.get_follow_stats(profile_user_id)
        collections = await self.collection_repo.get_public_user_collections(profile_user_id)
        items_count_map = await self.collection_repo.get_items_count_map(
            [item.id for item in collections if item.id is not None]
        )
        public_collections = [
            CollectionCard(
                id=collection.id,
                title=collection.title,
                description=collection.description,
                items_count=items_count_map.get(collection.id or 0, 0),
                is_public=collection.is_public,
                created_at=collection.created_at.strftime("%Y-%m-%d"),
                share_url=f"/collections/share/{collection.id}",
            )
            for collection in collections
            if collection.id is not None
        ]
        followers_preview = [
            FollowUserCard(
                user_id=user.id or 0,
                username=user.username,
                avatar_url=user.avatar_url,
                profile_url=f"/users/{user.id}",
            )
            for user in await self.user_repo.get_followers(profile_user_id, limit=6)
            if user.id is not None
        ]
        following_preview = [
            FollowUserCard(
                user_id=user.id or 0,
                username=user.username,
                avatar_url=user.avatar_url,
                profile_url=f"/users/{user.id}",
            )
            for user in await self.user_repo.get_followed_users(profile_user_id, limit=6)
            if user.id is not None
        ]
        is_following = (
            viewer_user_id is not None
            and viewer_user_id != profile_user_id
            and await self.user_repo.is_following(viewer_user_id, profile_user_id)
        )
        return await UserResult.success(
            PublicProfileOverview(
                profile=profile,
                public_collections=public_collections,
                followers_preview=followers_preview,
                following_preview=following_preview,
                followers_count=followers_count,
                following_count=following_count,
                is_following=is_following,
                can_follow=viewer_user_id is not None and viewer_user_id != profile_user_id,
            )
        )
