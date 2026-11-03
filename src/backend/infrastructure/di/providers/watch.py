"""Провайдеры сценариев просмотра."""

from __future__ import annotations

from dishka import Provider, Scope, provide

from backend.application.interface.unit_of_work import UnitOfWorkInterface
from backend.application.services import WatchSourceSyncService
from backend.application.use_cases import (
    AddAnimeCommentUseCase,
    AddWatchSourceUseCase,
    CompleteEpisodeUseCase,
    GetAnimeDetailUseCase,
    GetAnimeDiscussionUseCase,
    GetFavoriteIdsUseCase,
    GetUserAnimeLibraryUseCase,
    GetUserViewingHistoryUseCase,
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


class WatchUseCaseProvider(Provider):
    """Провайдер сценариев просмотра."""

    @provide(scope=Scope.REQUEST)
    async def get_watch_page(
        self,
        unit_of_work: UnitOfWorkInterface,
        anime_api_client: AnimeApiClient,
        watch_source_sync_service: WatchSourceSyncService,
    ) -> GetWatchPageUseCase:
        """Создать сценарий страницы просмотра."""
        return GetWatchPageUseCase(
            unit_of_work,
            anime_api_client,
            watch_source_sync_service,
        )

    @provide(scope=Scope.REQUEST)
    async def get_anime_discussion(
        self,
        unit_of_work: UnitOfWorkInterface,
    ) -> GetAnimeDiscussionUseCase:
        """Создать сценарий обсуждения аниме."""
        return GetAnimeDiscussionUseCase(unit_of_work)

    @provide(scope=Scope.REQUEST)
    async def add_watch_source(
        self,
        unit_of_work: UnitOfWorkInterface,
    ) -> AddWatchSourceUseCase:
        """Создать сценарий добавления источника."""
        return AddWatchSourceUseCase(unit_of_work)

    @provide(scope=Scope.REQUEST)
    async def sync_watch_sources(
        self,
        unit_of_work: UnitOfWorkInterface,
        anime_api_client: AnimeApiClient,
        watch_source_sync_service: WatchSourceSyncService,
    ) -> SyncWatchSourcesUseCase:
        """Создать сценарий синхронизации источников."""
        return SyncWatchSourcesUseCase(
            unit_of_work,
            anime_api_client,
            watch_source_sync_service,
        )

    @provide(scope=Scope.REQUEST)
    async def upsert_user_anime_status(
        self,
        unit_of_work: UnitOfWorkInterface,
        profile_overview_cache: ProfileOverviewCache,
    ) -> UpsertUserAnimeStatusUseCase:
        """Создать сценарий обновления статуса просмотра."""
        return UpsertUserAnimeStatusUseCase(unit_of_work, profile_overview_cache)

    @provide(scope=Scope.REQUEST)
    async def save_viewing_session(
        self,
        unit_of_work: UnitOfWorkInterface,
        profile_overview_cache: ProfileOverviewCache,
    ) -> SaveViewingSessionUseCase:
        """Создать сценарий сохранения сессии просмотра."""
        return SaveViewingSessionUseCase(unit_of_work, profile_overview_cache)

    @provide(scope=Scope.REQUEST)
    async def complete_episode(
        self,
        unit_of_work: UnitOfWorkInterface,
        profile_overview_cache: ProfileOverviewCache,
    ) -> CompleteEpisodeUseCase:
        """Создать сценарий завершения серии."""
        return CompleteEpisodeUseCase(unit_of_work, profile_overview_cache)

    @provide(scope=Scope.REQUEST)
    async def add_anime_comment(
        self,
        unit_of_work: UnitOfWorkInterface,
    ) -> AddAnimeCommentUseCase:
        """Создать сценарий добавления комментария к аниме."""
        return AddAnimeCommentUseCase(unit_of_work)

    @provide(scope=Scope.REQUEST)
    async def set_anime_comment_like(
        self,
        unit_of_work: UnitOfWorkInterface,
    ) -> SetAnimeCommentLikeUseCase:
        """Создать сценарий лайка комментария к аниме."""
        return SetAnimeCommentLikeUseCase(unit_of_work)

    @provide(scope=Scope.REQUEST)
    async def create_watch_highlight(
        self,
        unit_of_work: UnitOfWorkInterface,
        create_highlight: CreateHighlightUseCase,
    ) -> CreateWatchHighlightUseCase:
        """Создать сценарий создания хайлайта из плеера."""
        return CreateWatchHighlightUseCase(unit_of_work, create_highlight)

    @provide(scope=Scope.REQUEST)
    async def get_user_anime_library(
        self,
        unit_of_work: UnitOfWorkInterface,
        anime_api_client: AnimeApiClient,
    ) -> GetUserAnimeLibraryUseCase:
        """Создать сценарий чтения библиотеки просмотра."""
        return GetUserAnimeLibraryUseCase(unit_of_work, anime_api_client)

    @provide(scope=Scope.REQUEST)
    async def get_user_viewing_history(
        self,
        unit_of_work: UnitOfWorkInterface,
        anime_api_client: AnimeApiClient,
    ) -> GetUserViewingHistoryUseCase:
        """Создать сценарий чтения истории просмотров."""
        return GetUserViewingHistoryUseCase(unit_of_work, anime_api_client)

    @provide(scope=Scope.REQUEST)
    async def get_anime_detail(
        self,
        unit_of_work: UnitOfWorkInterface,
        watch_page_use_case: GetWatchPageUseCase,
        favorite_ids_use_case: GetFavoriteIdsUseCase,
    ) -> GetAnimeDetailUseCase:
        """Создать сценарий карточки тайтла для мобильного клиента."""
        return GetAnimeDetailUseCase(unit_of_work, watch_page_use_case, favorite_ids_use_case)
