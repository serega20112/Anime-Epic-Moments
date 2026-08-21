"""Request-scoped providers: session, repositories, and business services."""

from __future__ import annotations

from collections.abc import AsyncIterator

from dishka import Provider, Scope, provide
from sqlalchemy.ext.asyncio import AsyncSession

from backend.application.interface.unit_of_work import UnitOfWorkInterface
from backend.application.services import WatchSourceSyncService
from backend.application.services.recommendation_service import RecommendationService
from backend.infrastructure.cache import RecommendationCache
from backend.infrastructure.external import (
    AniBoomProvider,
    AniLibriaClient,
    AnimeApiClient,
    JustWatchClient,
    KodikClient,
    SamebandProvider,
)
from backend.infrastructure.external.youtube_client import YouTubeClient
from backend.infrastructure.files.database import get_session_factory
from backend.infrastructure.repositories.collection_repository import CollectionRepository
from backend.infrastructure.repositories.favorite_repository import FavoriteRepository
from backend.infrastructure.repositories.highlight_repository import HighlightRepository
from backend.infrastructure.repositories.moment_repository import MomentRepository
from backend.infrastructure.repositories.reaction_repository import ReactionRepository
from backend.infrastructure.repositories.support_repository import SupportRepository
from backend.infrastructure.repositories.user_repository import UserRepository
from backend.infrastructure.repositories.watch_repository import WatchRepository
from backend.infrastructure.unit_of_work import SqlAlchemyUnitOfWork


class RequestProvider(Provider):
    """Provide request-scoped repositories and services."""

    @provide(scope=Scope.REQUEST)
    async def session(self) -> AsyncIterator[AsyncSession]:
        """Provide an async database session.

        Yields:
            AsyncSession: Database session.
        """
        factory = await get_session_factory()
        async with factory() as session:
            yield session

    @provide(scope=Scope.REQUEST)
    async def unit_of_work(self, session: AsyncSession) -> UnitOfWorkInterface:
        """Provide the transaction boundary for a request.

        Args:
            session: Database session.

        Returns:
            UnitOfWorkInterface: Unit of work sharing the request session.
        """
        return SqlAlchemyUnitOfWork(session)

    @provide(scope=Scope.REQUEST)
    async def user_repository(self, session: AsyncSession) -> UserRepository:
        """Provide the user repository.

        Args:
            session: Database session.

        Returns:
            UserRepository: Configured repository.
        """
        return UserRepository(session)

    @provide(scope=Scope.REQUEST)
    async def highlight_repository(self, session: AsyncSession) -> HighlightRepository:
        """Provide the highlight repository.

        Args:
            session: Database session.

        Returns:
            HighlightRepository: Configured repository.
        """
        return HighlightRepository(session)

    @provide(scope=Scope.REQUEST)
    async def favorite_repository(self, session: AsyncSession) -> FavoriteRepository:
        """Provide the favorite repository.

        Args:
            session: Database session.

        Returns:
            FavoriteRepository: Configured repository.
        """
        return FavoriteRepository(session)

    @provide(scope=Scope.REQUEST)
    async def collection_repository(self, session: AsyncSession) -> CollectionRepository:
        """Provide the collection repository.

        Args:
            session: Database session.

        Returns:
            CollectionRepository: Configured repository.
        """
        return CollectionRepository(session)

    @provide(scope=Scope.REQUEST)
    async def watch_repository(self, session: AsyncSession) -> WatchRepository:
        """Provide the watch repository.

        Args:
            session: Database session.

        Returns:
            WatchRepository: Configured repository.
        """
        return WatchRepository(session)

    @provide(scope=Scope.REQUEST)
    async def support_repository(self, session: AsyncSession) -> SupportRepository:
        """Provide the support repository.

        Args:
            session: Database session.

        Returns:
            SupportRepository: Configured repository.
        """
        return SupportRepository(session)

    @provide(scope=Scope.REQUEST)
    async def reaction_repository(self, session: AsyncSession) -> ReactionRepository:
        """Provide the reaction repository.

        Args:
            session: Database session.

        Returns:
            ReactionRepository: Configured repository.
        """
        return ReactionRepository(session)

    @provide(scope=Scope.REQUEST)
    async def moment_repository(self, session: AsyncSession) -> MomentRepository:
        """Provide the moment repository.

        Args:
            session: Database session.

        Returns:
            MomentRepository: Configured repository.
        """
        return MomentRepository(session)

    @provide(scope=Scope.REQUEST)
    async def recommendation_service(
        self,
        favorite_repository: FavoriteRepository,
        highlight_repository: HighlightRepository,
        anime_api_client: AnimeApiClient,
        recommendation_cache: RecommendationCache,
    ) -> RecommendationService:
        """Provide the recommendation service.

        Args:
            favorite_repository: Favorite repository.
            highlight_repository: Highlight repository.
            anime_api_client: Anime API client.
            recommendation_cache: Recommendation cache.

        Returns:
            RecommendationService: Configured service.
        """
        return RecommendationService(
            favorite_repository,
            highlight_repository,
            anime_api_client,
            recommendation_cache,
        )

    @provide(scope=Scope.REQUEST)
    async def watch_source_sync_service(
        self,
        watch_repository: WatchRepository,
        kodik_client: KodikClient,
        anilibria_client: AniLibriaClient,
        sameband_provider: SamebandProvider,
        aniboom_provider: AniBoomProvider,
        youtube_client: YouTubeClient,
        justwatch_client: JustWatchClient,
    ) -> WatchSourceSyncService:
        """Provide the watch source sync service.

        Args:
            watch_repository: Watch repository.
            kodik_client: Kodik client.
            anilibria_client: AniLibria client.
            sameband_provider: SameBand provider.
            aniboom_provider: AniBoom provider.
            youtube_client: YouTube client.
            justwatch_client: JustWatch client.

        Returns:
            WatchSourceSyncService: Configured service.
        """
        return WatchSourceSyncService(
            watch_repository,
            [
                sameband_provider,
                aniboom_provider,
                kodik_client,
                anilibria_client,
                youtube_client,
                justwatch_client,
            ],
        )
