"""Провайдеры сценариев хайлайтов."""

from __future__ import annotations

from dishka import Provider, Scope, provide

from backend.application.interface.unit_of_work import UnitOfWorkInterface
from backend.application.services.recommendation_service import RecommendationService
from backend.application.use_cases.highlight.crud.create_highlight import CreateHighlightUseCase
from backend.application.use_cases.highlight.crud.delete_highlight import DeleteHighlightUseCase
from backend.application.use_cases.highlight.crud.edit_highlight import EditHighlightUseCase
from backend.application.use_cases.highlight.feed.get_highlight_feed import GetHighlightFeedUseCase
from backend.application.use_cases.highlight.feed.get_liked_highlights import (
    GetLikedHighlightsUseCase,
)
from backend.application.use_cases.highlight.feed.get_public_top_highlights import (
    GetPublicTopHighlightsUseCase,
)
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
from backend.application.use_cases.highlight.social.set_highlight_like import (
    SetHighlightLikeUseCase,
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


class HighlightUseCaseProvider(Provider):
    """Провайдер сценариев хайлайтов."""

    @provide(scope=Scope.REQUEST)
    async def create_highlight(
        self,
        unit_of_work: UnitOfWorkInterface,
        recommendation_service: RecommendationService,
        highlight_dashboard_cache: HighlightDashboardCache,
        profile_overview_cache: ProfileOverviewCache,
    ) -> CreateHighlightUseCase:
        """Создать сценарий создания хайлайта."""
        return CreateHighlightUseCase(
            unit_of_work,
            recommendation_service,
            highlight_dashboard_cache,
            profile_overview_cache,
        )

    @provide(scope=Scope.REQUEST)
    async def delete_highlight(
        self,
        unit_of_work: UnitOfWorkInterface,
        recommendation_service: RecommendationService,
        highlight_dashboard_cache: HighlightDashboardCache,
        profile_overview_cache: ProfileOverviewCache,
    ) -> DeleteHighlightUseCase:
        """Создать сценарий удаления хайлайта."""
        return DeleteHighlightUseCase(
            unit_of_work,
            recommendation_service,
            highlight_dashboard_cache,
            profile_overview_cache,
        )

    @provide(scope=Scope.REQUEST)
    async def edit_highlight(
        self,
        unit_of_work: UnitOfWorkInterface,
        recommendation_service: RecommendationService,
        highlight_dashboard_cache: HighlightDashboardCache,
        profile_overview_cache: ProfileOverviewCache,
    ) -> EditHighlightUseCase:
        """Создать сценарий правки хайлайта."""
        return EditHighlightUseCase(
            unit_of_work,
            recommendation_service,
            highlight_dashboard_cache,
            profile_overview_cache,
        )

    @provide(scope=Scope.REQUEST)
    async def get_user_highlights(
        self,
        unit_of_work: UnitOfWorkInterface,
        anime_api_client: AnimeApiClient,
    ) -> GetUserHighlightsUseCase:
        """Создать сценарий хайлайтов пользователя."""
        return GetUserHighlightsUseCase(unit_of_work, anime_api_client)

    @provide(scope=Scope.REQUEST)
    async def get_public_top_highlights(
        self,
        unit_of_work: UnitOfWorkInterface,
        anime_api_client: AnimeApiClient,
        highlight_dashboard_cache: HighlightDashboardCache,
    ) -> GetPublicTopHighlightsUseCase:
        """Создать сценарий популярных публичных хайлайтов."""
        return GetPublicTopHighlightsUseCase(
            unit_of_work,
            anime_api_client,
            highlight_dashboard_cache,
        )

    @provide(scope=Scope.REQUEST)
    async def get_saved_highlights(
        self,
        unit_of_work: UnitOfWorkInterface,
        anime_api_client: AnimeApiClient,
    ) -> GetSavedHighlightsUseCase:
        """Создать сценарий сохранённых хайлайтов."""
        return GetSavedHighlightsUseCase(unit_of_work, anime_api_client)

    @provide(scope=Scope.REQUEST)
    async def get_liked_highlights(
        self,
        unit_of_work: UnitOfWorkInterface,
        anime_api_client: AnimeApiClient,
    ) -> GetLikedHighlightsUseCase:
        """Создать сценарий лайкнутых хайлайтов."""
        return GetLikedHighlightsUseCase(unit_of_work, anime_api_client)

    @provide(scope=Scope.REQUEST)
    async def get_shared_highlight(
        self,
        unit_of_work: UnitOfWorkInterface,
        anime_api_client: AnimeApiClient,
    ) -> GetSharedHighlightUseCase:
        """Создать сценарий хайлайта по ссылке."""
        return GetSharedHighlightUseCase(unit_of_work, anime_api_client)

    @provide(scope=Scope.REQUEST)
    async def get_highlight_feed(
        self,
        unit_of_work: UnitOfWorkInterface,
        anime_api_client: AnimeApiClient,
    ) -> GetHighlightFeedUseCase:
        """Создать сценарий общей ленты хайлайтов."""
        return GetHighlightFeedUseCase(unit_of_work, anime_api_client)

    @provide(scope=Scope.REQUEST)
    async def get_following_highlights(
        self,
        unit_of_work: UnitOfWorkInterface,
        anime_api_client: AnimeApiClient,
    ) -> GetFollowingHighlightsUseCase:
        """Создать сценарий хайлайтов подписок."""
        return GetFollowingHighlightsUseCase(unit_of_work, anime_api_client)

    @provide(scope=Scope.REQUEST)
    async def set_highlight_like(
        self,
        unit_of_work: UnitOfWorkInterface,
        highlight_dashboard_cache: HighlightDashboardCache,
        profile_overview_cache: ProfileOverviewCache,
    ) -> SetHighlightLikeUseCase:
        """Создать сценарий лайка хайлайта."""
        return SetHighlightLikeUseCase(
            unit_of_work,
            highlight_dashboard_cache,
            profile_overview_cache,
        )

    @provide(scope=Scope.REQUEST)
    async def add_highlight_comment(
        self,
        unit_of_work: UnitOfWorkInterface,
        highlight_dashboard_cache: HighlightDashboardCache,
        profile_overview_cache: ProfileOverviewCache,
    ) -> AddHighlightCommentUseCase:
        """Создать сценарий добавления комментария к хайлайту."""
        return AddHighlightCommentUseCase(
            unit_of_work,
            highlight_dashboard_cache,
            profile_overview_cache,
        )

    @provide(scope=Scope.REQUEST)
    async def get_highlight_comments(
        self,
        unit_of_work: UnitOfWorkInterface,
    ) -> GetHighlightCommentsUseCase:
        """Создать сценарий комментариев хайлайта."""
        return GetHighlightCommentsUseCase(unit_of_work)

    @provide(scope=Scope.REQUEST)
    async def get_highlight_likers(
        self,
        unit_of_work: UnitOfWorkInterface,
    ) -> GetHighlightLikersUseCase:
        """Создать сценарий списка лайкнувших."""
        return GetHighlightLikersUseCase(unit_of_work)

    @provide(scope=Scope.REQUEST)
    async def get_highlight_notifications(
        self,
        unit_of_work: UnitOfWorkInterface,
    ) -> GetHighlightNotificationsUseCase:
        """Создать сценарий уведомлений по хайлайтам."""
        return GetHighlightNotificationsUseCase(unit_of_work)

    @provide(scope=Scope.REQUEST)
    async def set_saved_highlight(
        self,
        unit_of_work: UnitOfWorkInterface,
        profile_overview_cache: ProfileOverviewCache,
    ) -> SetSavedHighlightUseCase:
        """Создать сценарий сохранения хайлайта."""
        return SetSavedHighlightUseCase(unit_of_work, profile_overview_cache)
