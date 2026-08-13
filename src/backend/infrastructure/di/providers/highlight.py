"""Highlight use case providers."""

from __future__ import annotations

from dishka import Provider, Scope, provide

from backend.application.services.recommendation_service import RecommendationService
from backend.application.use_cases import (
    DeleteHighlightUseCase,
    GetLikedHighlightsUseCase,
    GetPublicTopHighlightsUseCase,
    SetHighlightLikeUseCase,
)
from backend.application.use_cases.highlight.add_highlight_comment import (
    AddHighlightCommentUseCase,
)
from backend.application.use_cases.highlight.create_highlight import CreateHighlightUseCase
from backend.application.use_cases.highlight.edit_highlight import EditHighlightUseCase
from backend.application.use_cases.highlight.get_highlight_comments import (
    GetHighlightCommentsUseCase,
)
from backend.application.use_cases.highlight.get_highlight_feed import GetHighlightFeedUseCase
from backend.application.use_cases.highlight.get_highlight_likers import GetHighlightLikersUseCase
from backend.application.use_cases.highlight.get_highlight_notifications import (
    GetHighlightNotificationsUseCase,
)
from backend.application.use_cases.highlight.get_saved_highlights import (
    GetSavedHighlightsUseCase,
)
from backend.application.use_cases.highlight.get_shared_highlight import (
    GetSharedHighlightUseCase,
)
from backend.application.use_cases.highlight.get_user_highlights import GetUserHighlightsUseCase
from backend.application.use_cases.highlight.set_saved_highlight import SetSavedHighlightUseCase
from backend.application.use_cases.user.get_following_highlights import (
    GetFollowingHighlightsUseCase,
)
from backend.domain.unit_of_work import UnitOfWorkInterface
from backend.infrastructure.cache import HighlightDashboardCache
from backend.infrastructure.cache.profile_overview_cache import ProfileOverviewCache
from backend.infrastructure.external import AnimeApiClient
from backend.infrastructure.repositories.favorite_repository import FavoriteRepository
from backend.infrastructure.repositories.highlight_repository import HighlightRepository
from backend.infrastructure.repositories.user_repository import UserRepository


class HighlightUseCaseProvider(Provider):
    """Provide highlight use cases."""

    @provide(scope=Scope.REQUEST)
    def create_highlight(
        self,
        highlight_repository: HighlightRepository,
        recommendation_service: RecommendationService,
        highlight_dashboard_cache: HighlightDashboardCache,
        profile_overview_cache: ProfileOverviewCache,
        unit_of_work: UnitOfWorkInterface,
    ) -> CreateHighlightUseCase:
        """Provide the create highlight use case.

        Args:
            highlight_repository: Highlight repository.
            recommendation_service: Recommendation service.
            highlight_dashboard_cache: Dashboard cache.
            profile_overview_cache: Profile overview cache.
            unit_of_work: Transaction boundary.

        Returns:
            CreateHighlightUseCase: Configured use case.
        """
        return CreateHighlightUseCase(
            highlight_repository,
            recommendation_service,
            highlight_dashboard_cache,
            profile_overview_cache,
            unit_of_work,
        )

    @provide(scope=Scope.REQUEST)
    def delete_highlight(
        self,
        highlight_repository: HighlightRepository,
        recommendation_service: RecommendationService,
        highlight_dashboard_cache: HighlightDashboardCache,
        profile_overview_cache: ProfileOverviewCache,
        unit_of_work: UnitOfWorkInterface,
    ) -> DeleteHighlightUseCase:
        """Provide the delete highlight use case.

        Args:
            highlight_repository: Highlight repository.
            recommendation_service: Recommendation service.
            highlight_dashboard_cache: Dashboard cache.
            profile_overview_cache: Profile overview cache.
            unit_of_work: Transaction boundary.

        Returns:
            DeleteHighlightUseCase: Configured use case.
        """
        return DeleteHighlightUseCase(
            highlight_repository,
            recommendation_service,
            highlight_dashboard_cache,
            profile_overview_cache,
            unit_of_work,
        )

    @provide(scope=Scope.REQUEST)
    def edit_highlight(
        self,
        highlight_repository: HighlightRepository,
        recommendation_service: RecommendationService,
        highlight_dashboard_cache: HighlightDashboardCache,
        profile_overview_cache: ProfileOverviewCache,
        unit_of_work: UnitOfWorkInterface,
    ) -> EditHighlightUseCase:
        """Provide the edit highlight use case.

        Args:
            highlight_repository: Highlight repository.
            recommendation_service: Recommendation service.
            highlight_dashboard_cache: Dashboard cache.
            profile_overview_cache: Profile overview cache.
            unit_of_work: Transaction boundary.

        Returns:
            EditHighlightUseCase: Configured use case.
        """
        return EditHighlightUseCase(
            highlight_repository,
            recommendation_service,
            highlight_dashboard_cache,
            profile_overview_cache,
            unit_of_work,
        )

    @provide(scope=Scope.REQUEST)
    def get_user_highlights(
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
    def get_public_top_highlights(
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
    def get_saved_highlights(
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
    def get_liked_highlights(
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
    def get_shared_highlight(
        self,
        highlight_repository: HighlightRepository,
        anime_api_client: AnimeApiClient,
        user_repository: UserRepository,
        unit_of_work: UnitOfWorkInterface,
    ) -> GetSharedHighlightUseCase:
        """Provide the get shared highlight use case.

        Args:
            highlight_repository: Highlight repository.
            anime_api_client: Anime API client.
            user_repository: User repository.
            unit_of_work: Transaction boundary.

        Returns:
            GetSharedHighlightUseCase: Configured use case.
        """
        return GetSharedHighlightUseCase(
            highlight_repository,
            anime_api_client,
            user_repository,
            unit_of_work,
        )

    @provide(scope=Scope.REQUEST)
    def get_highlight_feed(
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
    def get_following_highlights(
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
    def set_highlight_like(
        self,
        highlight_repository: HighlightRepository,
        highlight_dashboard_cache: HighlightDashboardCache,
        profile_overview_cache: ProfileOverviewCache,
        unit_of_work: UnitOfWorkInterface,
    ) -> SetHighlightLikeUseCase:
        """Provide the set highlight like use case.

        Args:
            highlight_repository: Highlight repository.
            highlight_dashboard_cache: Dashboard cache.
            profile_overview_cache: Profile overview cache.
            unit_of_work: Transaction boundary.

        Returns:
            SetHighlightLikeUseCase: Configured use case.
        """
        return SetHighlightLikeUseCase(
            highlight_repository,
            highlight_dashboard_cache,
            profile_overview_cache,
            unit_of_work,
        )

    @provide(scope=Scope.REQUEST)
    def add_highlight_comment(
        self,
        highlight_repository: HighlightRepository,
        highlight_dashboard_cache: HighlightDashboardCache,
        profile_overview_cache: ProfileOverviewCache,
        unit_of_work: UnitOfWorkInterface,
    ) -> AddHighlightCommentUseCase:
        """Provide the add highlight comment use case.

        Args:
            highlight_repository: Highlight repository.
            highlight_dashboard_cache: Dashboard cache.
            profile_overview_cache: Profile overview cache.
            unit_of_work: Transaction boundary.

        Returns:
            AddHighlightCommentUseCase: Configured use case.
        """
        return AddHighlightCommentUseCase(
            highlight_repository,
            highlight_dashboard_cache,
            profile_overview_cache,
            unit_of_work,
        )

    @provide(scope=Scope.REQUEST)
    def get_highlight_comments(
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
    def get_highlight_likers(
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
    def get_highlight_notifications(
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
    def set_saved_highlight(
        self,
        highlight_repository: HighlightRepository,
        profile_overview_cache: ProfileOverviewCache,
        unit_of_work: UnitOfWorkInterface,
    ) -> SetSavedHighlightUseCase:
        """Provide the set saved highlight use case.

        Args:
            highlight_repository: Highlight repository.
            profile_overview_cache: Profile overview cache.
            unit_of_work: Transaction boundary.

        Returns:
            SetSavedHighlightUseCase: Configured use case.
        """
        return SetSavedHighlightUseCase(highlight_repository, profile_overview_cache, unit_of_work)
