"""Watch use case providers."""

from __future__ import annotations

from dishka import Provider, Scope, provide

from backend.application.services import WatchSourceSyncService
from backend.application.use_cases import (
    AddAnimeCommentUseCase,
    AddWatchSourceUseCase,
    GetWatchPageUseCase,
    SetAnimeCommentLikeUseCase,
    SyncWatchSourcesUseCase,
    UpsertUserAnimeStatusUseCase,
)
from backend.application.use_cases.highlight.create_highlight import CreateHighlightUseCase
from backend.application.use_cases.watch.create_watch_highlight import (
    CreateWatchHighlightUseCase,
)
from backend.application.use_cases.watch.save_viewing_session import SaveViewingSessionUseCase
from backend.domain.unit_of_work import UnitOfWorkInterface
from backend.infrastructure.cache.profile_overview_cache import ProfileOverviewCache
from backend.infrastructure.external import AnimeApiClient
from backend.infrastructure.repositories.highlight_repository import HighlightRepository
from backend.infrastructure.repositories.watch_repository import WatchRepository


class WatchUseCaseProvider(Provider):
    """Provide watch use cases."""

    @provide(scope=Scope.REQUEST)
    def get_watch_page(
        self,
        watch_repository: WatchRepository,
        highlight_repository: HighlightRepository,
        anime_api_client: AnimeApiClient,
        watch_source_sync_service: WatchSourceSyncService,
        unit_of_work: UnitOfWorkInterface,
    ) -> GetWatchPageUseCase:
        """Provide the get watch page use case.

        Args:
            watch_repository: Watch repository.
            highlight_repository: Highlight repository.
            anime_api_client: Anime API client.
            watch_source_sync_service: Watch source sync service.
            unit_of_work: Transaction boundary.

        Returns:
            GetWatchPageUseCase: Configured use case.
        """
        return GetWatchPageUseCase(
            watch_repository,
            highlight_repository,
            anime_api_client,
            watch_source_sync_service,
            unit_of_work,
        )

    @provide(scope=Scope.REQUEST)
    def add_watch_source(
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
    def sync_watch_sources(
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
    def upsert_user_anime_status(
        self,
        watch_repository: WatchRepository,
        profile_overview_cache: ProfileOverviewCache,
        unit_of_work: UnitOfWorkInterface,
    ) -> UpsertUserAnimeStatusUseCase:
        """Provide the upsert user anime status use case.

        Args:
            watch_repository: Watch repository.
            profile_overview_cache: Profile overview cache.
            unit_of_work: Transaction boundary.

        Returns:
            UpsertUserAnimeStatusUseCase: Configured use case.
        """
        return UpsertUserAnimeStatusUseCase(
            watch_repository,
            profile_overview_cache,
            unit_of_work,
        )

    @provide(scope=Scope.REQUEST)
    def save_viewing_session(
        self,
        watch_repository: WatchRepository,
        profile_overview_cache: ProfileOverviewCache,
        unit_of_work: UnitOfWorkInterface,
    ) -> SaveViewingSessionUseCase:
        """Provide the save viewing session use case.

        Args:
            watch_repository: Watch repository.
            profile_overview_cache: Profile overview cache.
            unit_of_work: Transaction boundary.

        Returns:
            SaveViewingSessionUseCase: Configured use case.
        """
        return SaveViewingSessionUseCase(
            watch_repository,
            profile_overview_cache,
            unit_of_work,
        )

    @provide(scope=Scope.REQUEST)
    def add_anime_comment(
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
    def set_anime_comment_like(
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
    def create_watch_highlight(
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
