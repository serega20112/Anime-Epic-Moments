"""Highlight use case providers."""

from __future__ import annotations

from dishka import Provider, Scope, provide

from backend.application.interface.unit_of_work import UnitOfWorkInterface
from backend.application.services.recommendation_service import RecommendationService
from backend.application.use_cases import (
    DeleteHighlightUseCase,
    GetLikedHighlightsUseCase,
    GetPublicTopHighlightsUseCase,
    SetHighlightLikeUseCase,
)
from backend.application.use_cases.highlight.crud.create_highlight import CreateHighlightUseCase
from backend.application.use_cases.highlight.crud.edit_highlight import EditHighlightUseCase
from backend.application.use_cases.highlight.feed.get_highlight_feed import GetHighlightFeedUseCase
from backend.application.use_cases.highlight.feed.get_saved_highlights import (
    GetSavedHighlightsUseCase,
)
from backend.application.use_cases.highlight.feed.get_shared_highlight import (
    GetSharedHighlightUseCase,
)
from backend.application.use_cases.highlight.feed.get_user_highlights import (
    GetUserHighlightsUseCase,
)
from backend.application.use_cases.highlight.social.add_highlight_comment import (
    AddHighlightCommentUseCase,
)
from backend.application.use_cases.highlight.social.get_highlight_comments import (
    GetHighlightCommentsUseCase,
)
from backend.application.use_cases.highlight.social.get_highlight_likers import (
    GetHighlightLikersUseCase,
)
from backend.application.use_cases.highlight.social.get_highlight_notifications import (
    GetHighlightNotificationsUseCase,
)
from backend.application.use_cases.highlight.social.set_saved_highlight import (
    SetSavedHighlightUseCase,
)
from backend.application.use_cases.user.get_following_highlights import (
    GetFollowingHighlightsUseCase,
)
from backend.infrastructure.cache import HighlightDashboardCache
from backend.infrastructure.cache.profile_overview_cache import ProfileOverviewCache
from backend.infrastructure.external import AnimeApiClient
from backend.infrastructure.repositories.favorite_repository import FavoriteRepository
from backend.infrastructure.repositories.highlight_repository import HighlightRepository
from backend.infrastructure.repositories.user_repository import UserRepository


class HighlightUseCaseProvider(Provider):
    """Provide highlight use cases."""

    @provide(scope=Scope.REQUEST)
    async def create_highlight(
        self,
        highlight_repository: HighlightRepository,
        unit_of_work: UnitOfWorkInterface,
        recommendation_service: RecommendationService,
        highlight_dashboard_cache: HighlightDashboardCache,
        profile_overview_cache: ProfileOverviewCache,
    ) -> CreateHighlightUseCase:
        """Provide the create highlight use case.

        Args:
            highlight_repository: Highlight repository.
            unit_of_work: Transaction boundary.
            recommendation_service: Recommendation service.
            highlight_dashboard_cache: Dashboard cache.
            profile_overview_cache: Profile overview cache.

        Returns:
            CreateHighlightUseCase: Configured use case.
        """
        return CreateHighlightUseCase(
            highlight_repository,
            unit_of_work,
            recommendation_service,
            highlight_dashboard_cache,
            profile_overview_cache,
        )

    @provide(scope=Scope.REQUEST)
    async def delete_highlight(
        self,
        highlight_repository: HighlightRepository,
        unit_of_work: UnitOfWorkInterface,
        recommendation_service: RecommendationService,
        highlight_dashboard_cache: HighlightDashboardCache,
        profile_overview_cache: ProfileOverviewCache,
    ) -> DeleteHighlightUseCase:
        """Provide the delete highlight use case.

        Args:
            highlight_repository: Highlight repository.
            unit_of_work: Transaction boundary.
            recommendation_service: Recommendation service.
            highlight_dashboard_cache: Dashboard cache.
            profile_overview_cache: Profile overview cache.

        Returns:
            DeleteHighlightUseCase: Configured use case.
        """
        return DeleteHighlightUseCase(
            highlight_repository,
            unit_of_work,
            recommendation_service,
            highlight_dashboard_cache,
            profile_overview_cache,
        )

    @provide(scope=Scope.REQUEST)
    async def edit_highlight(
        self,
        highlight_repository: HighlightRepository,
        unit_of_work: UnitOfWorkInterface,
        recommendation_service: RecommendationService,
        highlight_dashboard_cache: HighlightDashboardCache,
        profile_overview_cache: ProfileOverviewCache,
    ) -> EditHighlightUseCase:
        """Provide the edit highlight use case.

        Args:
            highlight_repository: Highlight repository.
            unit_of_work: Transaction boundary.
            recommendation_service: Recommendation service.
            highlight_dashboard_cache: Dashboard cache.
            profile_overview_cache: Profile overview cache.

        Returns:
            EditHighlightUseCase: Configured use case.
        """
        return EditHighlightUseCase(
            highlight_repository,
            unit_of_work,
            recommendation_service,
            highlight_dashboard_cache,
            profile_overview_cache,
        )

    @provide(scope=Scope.REQUEST)
    async def get_user_highlights(
        self,
        highlight_repository: HighlightRepository,
        anime_api_client: AnimeApiClient,
        user_repository: UserRepository,
    ) -> GetUserHighlightsUseCase:
        """Provide the get user highlights use case.

        Args:
            highlight_repository: Highlight repository.
            anime_api_client: Anime API client.
            user_repository: User repository.

        Returns:
            GetUserHighlightsUseCase: Configured use case.
        """
        return GetUserHighlightsUseCase(
            highlight_repository,
            anime_api_client,
            user_repository,
        )

    @provide(scope=Scope.REQUEST)
    async def get_public_top_highlights(
        self,
        highlight_repository: HighlightRepository,
        anime_api_client: AnimeApiClient,
        highlight_dashboard_cache: HighlightDashboardCache,
        user_repository: UserRepository,
    ) -> GetPublicTopHighlightsUseCase:
        """Provide the get public top highlights use case.

        Args:
            highlight_repository: Highlight repository.
            anime_api_client: Anime API client.
            highlight_dashboard_cache: Dashboard cache.
            user_repository: User repository.

        Returns:
            GetPublicTopHighlightsUseCase: Configured use case.
        """
        return GetPublicTopHighlightsUseCase(
            highlight_repository,
            anime_api_client,
            highlight_dashboard_cache,
            user_repository,
        )

    @provide(scope=Scope.REQUEST)
    async def get_saved_highlights(
        self,
        highlight_repository: HighlightRepository,
        anime_api_client: AnimeApiClient,
        user_repository: UserRepository,
    ) -> GetSavedHighlightsUseCase:
        """Provide the get saved highlights use case.

        Args:
            highlight_repository: Highlight repository.
            anime_api_client: Anime API client.
            user_repository: User repository.

        Returns:
            GetSavedHighlightsUseCase: Configured use case.
        """
        return GetSavedHighlightsUseCase(
            highlight_repository,
            anime_api_client,
            user_repository,
        )

    @provide(scope=Scope.REQUEST)
    async def get_liked_highlights(
        self,
        highlight_repository: HighlightRepository,
        anime_api_client: AnimeApiClient,
        user_repository: UserRepository,
    ) -> GetLikedHighlightsUseCase:
        """Provide the get liked highlights use case.

        Args:
            highlight_repository: Highlight repository.
            anime_api_client: Anime API client.
            user_repository: User repository.

        Returns:
            GetLikedHighlightsUseCase: Configured use case.
        """
        return GetLikedHighlightsUseCase(
            highlight_repository,
            anime_api_client,
            user_repository,
        )

    @provide(scope=Scope.REQUEST)
    async def get_shared_highlight(
        self,
        highlight_repository: HighlightRepository,
        anime_api_client: AnimeApiClient,
        unit_of_work: UnitOfWorkInterface,
        user_repository: UserRepository,
    ) -> GetSharedHighlightUseCase:
        """Provide the get shared highlight use case.

        Args:
            highlight_repository: Highlight repository.
            anime_api_client: Anime API client.
            unit_of_work: Transaction boundary.
            user_repository: User repository.

        Returns:
            GetSharedHighlightUseCase: Configured use case.
        """
        return GetSharedHighlightUseCase(
            highlight_repository,
            anime_api_client,
            unit_of_work,
            user_repository,
        )

    @provide(scope=Scope.REQUEST)
    async def get_highlight_feed(
        self,
        highlight_repository: HighlightRepository,
        anime_api_client: AnimeApiClient,
        favorite_repository: FavoriteRepository,
        user_repository: UserRepository,
    ) -> GetHighlightFeedUseCase:
        """Provide the get highlight feed use case.

        Args:
            highlight_repository: Highlight repository.
            anime_api_client: Anime API client.
            favorite_repository: Favorite repository.
            user_repository: User repository.

        Returns:
            GetHighlightFeedUseCase: Configured use case.
        """
        return GetHighlightFeedUseCase(
            highlight_repository,
            anime_api_client,
            favorite_repository,
            user_repository,
        )

    @provide(scope=Scope.REQUEST)
    async def get_following_highlights(
        self,
        highlight_repository: HighlightRepository,
        anime_api_client: AnimeApiClient,
        user_repository: UserRepository,
    ) -> GetFollowingHighlightsUseCase:
        """Provide the get following highlights use case.

        Args:
            highlight_repository: Highlight repository.
            anime_api_client: Anime API client.
            user_repository: User repository.

        Returns:
            GetFollowingHighlightsUseCase: Configured use case.
        """
        return GetFollowingHighlightsUseCase(
            highlight_repository,
            anime_api_client,
            user_repository,
        )

    @provide(scope=Scope.REQUEST)
    async def set_highlight_like(
        self,
        highlight_repository: HighlightRepository,
        unit_of_work: UnitOfWorkInterface,
        highlight_dashboard_cache: HighlightDashboardCache,
        profile_overview_cache: ProfileOverviewCache,
    ) -> SetHighlightLikeUseCase:
        """Provide the set highlight like use case.

        Args:
            highlight_repository: Highlight repository.
            unit_of_work: Transaction boundary.
            highlight_dashboard_cache: Dashboard cache.
            profile_overview_cache: Profile overview cache.

        Returns:
            SetHighlightLikeUseCase: Configured use case.
        """
        return SetHighlightLikeUseCase(
            highlight_repository,
            unit_of_work,
            highlight_dashboard_cache,
            profile_overview_cache,
        )

    @provide(scope=Scope.REQUEST)
    async def add_highlight_comment(
        self,
        highlight_repository: HighlightRepository,
        unit_of_work: UnitOfWorkInterface,
        highlight_dashboard_cache: HighlightDashboardCache,
        profile_overview_cache: ProfileOverviewCache,
    ) -> AddHighlightCommentUseCase:
        """Provide the add highlight comment use case.

        Args:
            highlight_repository: Highlight repository.
            unit_of_work: Transaction boundary.
            highlight_dashboard_cache: Dashboard cache.
            profile_overview_cache: Profile overview cache.

        Returns:
            AddHighlightCommentUseCase: Configured use case.
        """
        return AddHighlightCommentUseCase(
            highlight_repository,
            unit_of_work,
            highlight_dashboard_cache,
            profile_overview_cache,
        )

    @provide(scope=Scope.REQUEST)
    async def get_highlight_comments(
        self,
        highlight_repository: HighlightRepository,
    ) -> GetHighlightCommentsUseCase:
        """Provide the get highlight comments use case.

        Args:
            highlight_repository: Highlight repository.

        Returns:
            GetHighlightCommentsUseCase: Configured use case.
        """
        return GetHighlightCommentsUseCase(highlight_repository)

    @provide(scope=Scope.REQUEST)
    async def get_highlight_likers(
        self,
        highlight_repository: HighlightRepository,
    ) -> GetHighlightLikersUseCase:
        """Provide the get highlight likers use case.

        Args:
            highlight_repository: Highlight repository.

        Returns:
            GetHighlightLikersUseCase: Configured use case.
        """
        return GetHighlightLikersUseCase(highlight_repository)

    @provide(scope=Scope.REQUEST)
    async def get_highlight_notifications(
        self,
        highlight_repository: HighlightRepository,
    ) -> GetHighlightNotificationsUseCase:
        """Provide the get highlight notifications use case.

        Args:
            highlight_repository: Highlight repository.

        Returns:
            GetHighlightNotificationsUseCase: Configured use case.
        """
        return GetHighlightNotificationsUseCase(highlight_repository)

    @provide(scope=Scope.REQUEST)
    async def set_saved_highlight(
        self,
        highlight_repository: HighlightRepository,
        unit_of_work: UnitOfWorkInterface,
        profile_overview_cache: ProfileOverviewCache,
    ) -> SetSavedHighlightUseCase:
        """Provide the set saved highlight use case.

        Args:
            highlight_repository: Highlight repository.
            unit_of_work: Transaction boundary.
            profile_overview_cache: Profile overview cache.

        Returns:
            SetSavedHighlightUseCase: Configured use case.
        """
        return SetSavedHighlightUseCase(highlight_repository, unit_of_work, profile_overview_cache)
