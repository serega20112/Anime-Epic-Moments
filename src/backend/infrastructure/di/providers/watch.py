"""Watch use case providers."""

from __future__ import annotations

from dishka import Provider, Scope, provide

from backend.application.interface.unit_of_work import UnitOfWorkInterface
from backend.application.services import WatchSourceSyncService
from backend.application.use_cases import (
    AddAnimeCommentUseCase,
    AddWatchSourceUseCase,
    CompleteEpisodeUseCase,
    GetAnimeDiscussionUseCase,
    GetWatchPageUseCase,
    SetAnimeCommentLikeUseCase,
    SyncWatchSourcesUseCase,
    UpsertUserAnimeStatusUseCase,
)
from backend.application.use_cases.highlight.crud.create_highlight import CreateHighlightUseCase
from backend.application.use_cases.watch.highlight.create_watch_highlight import (
    CreateWatchHighlightUseCase,
)
from backend.application.use_cases.watch.session.save_viewing_session import (
    SaveViewingSessionUseCase,
)
from backend.infrastructure.cache.profile_overview_cache import ProfileOverviewCache
from backend.infrastructure.external import AnimeApiClient
from backend.infrastructure.repositories.highlight_repository import HighlightRepository
from backend.infrastructure.repositories.rating_repository import RatingRepository
from backend.infrastructure.repositories.watch_repository import WatchRepository


class WatchUseCaseProvider(Provider):
    """Provide watch use cases."""

    @provide(scope=Scope.REQUEST)
    async def get_watch_page(
        self,
        watch_repository: WatchRepository,
        highlight_repository: HighlightRepository,
        anime_api_client: AnimeApiClient,
        watch_source_sync_service: WatchSourceSyncService,
        unit_of_work: UnitOfWorkInterface,
        rating_repository: RatingRepository,
    ) -> GetWatchPageUseCase:
        """Provide the get watch page use case.

        Args:
            watch_repository: Watch repository.
            highlight_repository: Highlight repository.
            anime_api_client: Anime API client.
            watch_source_sync_service: Watch source sync service.
            unit_of_work: Transaction boundary.
            rating_repository: Rating repository.

        Returns:
            GetWatchPageUseCase: Configured use case.
        """
        return GetWatchPageUseCase(
            watch_repository,
            highlight_repository,
            anime_api_client,
            watch_source_sync_service,
            unit_of_work,
            rating_repository,
        )

    @provide(scope=Scope.REQUEST)
    async def get_anime_discussion(
        self,
        watch_repository: WatchRepository,
    ) -> GetAnimeDiscussionUseCase:
        """Provide the get anime discussion use case.

        Args:
            watch_repository: Watch repository.

        Returns:
            GetAnimeDiscussionUseCase: Configured use case.
        """
        return GetAnimeDiscussionUseCase(watch_repository)

    @provide(scope=Scope.REQUEST)
    async def add_watch_source(
        self,
        watch_repository: WatchRepository,
        unit_of_work: UnitOfWorkInterface,
    ) -> AddWatchSourceUseCase:
        """Provide the add watch source use case.

        Args:
            watch_repository: Watch repository.
            unit_of_work: Transaction boundary.

        Returns:
            AddWatchSourceUseCase: Configured use case.
        """
        return AddWatchSourceUseCase(watch_repository, unit_of_work)

    @provide(scope=Scope.REQUEST)
    async def sync_watch_sources(
        self,
        anime_api_client: AnimeApiClient,
        watch_source_sync_service: WatchSourceSyncService,
        unit_of_work: UnitOfWorkInterface,
    ) -> SyncWatchSourcesUseCase:
        """Provide the sync watch sources use case.

        Args:
            anime_api_client: Anime API client.
            watch_source_sync_service: Watch source sync service.
            unit_of_work: Transaction boundary.

        Returns:
            SyncWatchSourcesUseCase: Configured use case.
        """
        return SyncWatchSourcesUseCase(
            anime_api_client,
            watch_source_sync_service,
            unit_of_work,
        )

    @provide(scope=Scope.REQUEST)
    async def upsert_user_anime_status(
        self,
        watch_repository: WatchRepository,
        unit_of_work: UnitOfWorkInterface,
        profile_overview_cache: ProfileOverviewCache,
    ) -> UpsertUserAnimeStatusUseCase:
        """Provide the upsert user anime status use case.

        Args:
            watch_repository: Watch repository.
            unit_of_work: Transaction boundary.
            profile_overview_cache: Profile overview cache.

        Returns:
            UpsertUserAnimeStatusUseCase: Configured use case.
        """
        return UpsertUserAnimeStatusUseCase(
            watch_repository,
            unit_of_work,
            profile_overview_cache,
        )

    @provide(scope=Scope.REQUEST)
    async def save_viewing_session(
        self,
        watch_repository: WatchRepository,
        unit_of_work: UnitOfWorkInterface,
        profile_overview_cache: ProfileOverviewCache,
    ) -> SaveViewingSessionUseCase:
        """Provide the save viewing session use case.

        Args:
            watch_repository: Watch repository.
            unit_of_work: Transaction boundary.
            profile_overview_cache: Profile overview cache.

        Returns:
            SaveViewingSessionUseCase: Configured use case.
        """
        return SaveViewingSessionUseCase(
            watch_repository,
            unit_of_work,
            profile_overview_cache,
        )

    @provide(scope=Scope.REQUEST)
    async def complete_episode(
        self,
        watch_repository: WatchRepository,
        unit_of_work: UnitOfWorkInterface,
        profile_overview_cache: ProfileOverviewCache,
    ) -> CompleteEpisodeUseCase:
        """Provide the complete episode use case.

        Args:
            watch_repository: Watch repository.
            unit_of_work: Transaction boundary.
            profile_overview_cache: Profile overview cache.

        Returns:
            CompleteEpisodeUseCase: Configured use case.
        """
        return CompleteEpisodeUseCase(
            watch_repository,
            unit_of_work,
            profile_overview_cache,
        )

    @provide(scope=Scope.REQUEST)
    async def add_anime_comment(
        self,
        watch_repository: WatchRepository,
        unit_of_work: UnitOfWorkInterface,
    ) -> AddAnimeCommentUseCase:
        """Provide the add anime comment use case.

        Args:
            watch_repository: Watch repository.
            unit_of_work: Transaction boundary.

        Returns:
            AddAnimeCommentUseCase: Configured use case.
        """
        return AddAnimeCommentUseCase(watch_repository, unit_of_work)

    @provide(scope=Scope.REQUEST)
    async def set_anime_comment_like(
        self,
        watch_repository: WatchRepository,
        unit_of_work: UnitOfWorkInterface,
    ) -> SetAnimeCommentLikeUseCase:
        """Provide the set anime comment like use case.

        Args:
            watch_repository: Watch repository.
            unit_of_work: Transaction boundary.

        Returns:
            SetAnimeCommentLikeUseCase: Configured use case.
        """
        return SetAnimeCommentLikeUseCase(watch_repository, unit_of_work)

    @provide(scope=Scope.REQUEST)
    async def create_watch_highlight(
        self,
        create_highlight: CreateHighlightUseCase,
        watch_repository: WatchRepository,
        unit_of_work: UnitOfWorkInterface,
    ) -> CreateWatchHighlightUseCase:
        """Provide the create watch highlight use case.

        Args:
            create_highlight: Create highlight use case.
            watch_repository: Watch repository.
            unit_of_work: Transaction boundary.

        Returns:
            CreateWatchHighlightUseCase: Configured use case.
        """
        return CreateWatchHighlightUseCase(create_highlight, watch_repository, unit_of_work)
