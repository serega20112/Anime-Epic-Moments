"""Провайдеры уровня запроса: сессия, репозитории и бизнес-сервисы."""

from __future__ import annotations

from collections.abc import AsyncIterator

from dishka import Provider, Scope, provide
from sqlalchemy.ext.asyncio import AsyncSession

from backend.application.interface.repositories.user_repository import (
    UserRepository as UserRepositoryPort,
)
from backend.application.interface.unit_of_work import UnitOfWorkInterface
from backend.application.services import WatchSourceSyncService
from backend.application.services.recommendation_service import RecommendationService
from backend.infrastructure.cache import RecommendationCache, WatchSourceCaches
from backend.infrastructure.database.repositories.collection_repository import CollectionRepository
from backend.infrastructure.database.repositories.favorite_repository import FavoriteRepository
from backend.infrastructure.database.repositories.highlight_repository import HighlightRepository
from backend.infrastructure.database.repositories.moment_repository import MomentRepository
from backend.infrastructure.database.repositories.rating_repository import RatingRepository
from backend.infrastructure.database.repositories.reaction_repository import ReactionRepository
from backend.infrastructure.database.repositories.support_repository import SupportRepository
from backend.infrastructure.database.repositories.user_repository import UserRepository
from backend.infrastructure.database.repositories.watch_repository import WatchRepository
from backend.infrastructure.database.session import get_session_factory
from backend.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork
from backend.infrastructure.external import (
    AniBoomProvider,
    AniLibriaClient,
    AnimeApiClient,
    AnimeGoProvider,
    EpornerProvider,
    HanimeProvider,
    HDRezkaProvider,
    HentaigasmProvider,
    JustWatchClient,
    KinoboxProvider,
    KodikClient,
    SamebandProvider,
)
from backend.infrastructure.external.video import YouTubeClient


class RequestProvider(Provider):
    """Провайдер репозиториев и сервисов уровня запроса."""

    @provide(scope=Scope.REQUEST)
    async def session(self) -> AsyncIterator[AsyncSession]:
        """Открыть асинхронную сессию базы данных на время запроса."""
        factory = await get_session_factory()
        async with factory() as session:
            yield session

    @provide(scope=Scope.REQUEST)
    async def unit_of_work(self, session: AsyncSession) -> UnitOfWorkInterface:
        """Создать единицу работы с общей сессией запроса."""
        return SqlAlchemyUnitOfWork(session)

    @provide(scope=Scope.REQUEST)
    async def user_repository(self, session: AsyncSession) -> UserRepository:
        """Создать репозиторий пользователей."""
        return UserRepository(session)

    @provide(scope=Scope.REQUEST)
    async def user_repository_port(self, repository: UserRepository) -> UserRepositoryPort:
        """Опубликовать репозиторий пользователей через его порт.

        Args:
            repository: Конкретный репозиторий пользователей.

        Returns:
            UserRepositoryPort: Тот же репозиторий под абстракцией порта.
        """
        return repository

    @provide(scope=Scope.REQUEST)
    async def highlight_repository(self, session: AsyncSession) -> HighlightRepository:
        """Создать репозиторий хайлайтов."""
        return HighlightRepository(session)

    @provide(scope=Scope.REQUEST)
    async def favorite_repository(self, session: AsyncSession) -> FavoriteRepository:
        """Создать репозиторий избранного."""
        return FavoriteRepository(session)

    @provide(scope=Scope.REQUEST)
    async def collection_repository(self, session: AsyncSession) -> CollectionRepository:
        """Создать репозиторий коллекций."""
        return CollectionRepository(session)

    @provide(scope=Scope.REQUEST)
    async def watch_repository(self, session: AsyncSession) -> WatchRepository:
        """Создать репозиторий просмотра."""
        return WatchRepository(session)

    @provide(scope=Scope.REQUEST)
    async def rating_repository(self, session: AsyncSession) -> RatingRepository:
        """Создать репозиторий оценок."""
        return RatingRepository(session)

    @provide(scope=Scope.REQUEST)
    async def support_repository(self, session: AsyncSession) -> SupportRepository:
        """Создать репозиторий обращений в поддержку."""
        return SupportRepository(session)

    @provide(scope=Scope.REQUEST)
    async def reaction_repository(self, session: AsyncSession) -> ReactionRepository:
        """Создать репозиторий реакций."""
        return ReactionRepository(session)

    @provide(scope=Scope.REQUEST)
    async def moment_repository(self, session: AsyncSession) -> MomentRepository:
        """Создать репозиторий моментов просмотра."""
        return MomentRepository(session)

    @provide(scope=Scope.REQUEST)
    async def recommendation_service(
        self,
        anime_api_client: AnimeApiClient,
        recommendation_cache: RecommendationCache,
    ) -> RecommendationService:
        """Создать сервис рекомендаций."""
        return RecommendationService(
            anime_api_client,
            recommendation_cache,
        )

    @provide(scope=Scope.REQUEST)
    async def watch_source_sync_service(
        self,
        kodik_client: KodikClient,
        anilibria_client: AniLibriaClient,
        sameband_provider: SamebandProvider,
        aniboom_provider: AniBoomProvider,
        hanime_provider: HanimeProvider,
        animego_provider: AnimeGoProvider,
        kinobox_provider: KinoboxProvider,
        hdrezka_provider: HDRezkaProvider,
        hentaigasm_provider: HentaigasmProvider,
        eporner_provider: EpornerProvider,
        youtube_client: YouTubeClient,
        justwatch_client: JustWatchClient,
        caches: WatchSourceCaches,
    ) -> WatchSourceSyncService:
        """Создать сервис синхронизации источников просмотра.

        Args:
            kodik_client: Клиент Kodik.
            anilibria_client: Клиент AniLibria.
            sameband_provider: Провайдер SameBand.
            aniboom_provider: Провайдер AniBoom.
            hanime_provider: Провайдер Hanime.tv.
            animego_provider: Скрапер AnimeGo, питающий извлекатели Sibnet и
                AniBoom.
            kinobox_provider: Провайдер-агрегатор Kinobox.
            hdrezka_provider: Парсер HDRezka.
            hentaigasm_provider: Провайдер хентая Hentaigasm с прямыми MP4.
            eporner_provider: API-провайдер хентая Eporner для тайтлов, где
                Hanime недоступен.
            youtube_client: Клиент YouTube.
            justwatch_client: Клиент JustWatch.
            caches: Внутрипроцессные кэши сервиса.

        Returns:
            WatchSourceSyncService: Настроенный сервис.
        """
        return WatchSourceSyncService(
            [
                animego_provider,
                kodik_client,
                kinobox_provider,
                hdrezka_provider,
                sameband_provider,
                aniboom_provider,
                hanime_provider,
                hentaigasm_provider,
                eporner_provider,
                anilibria_client,
                youtube_client,
                justwatch_client,
            ],
            empty_result_cache=caches.empty_results,
            availability_cache=caches.availability,
        )
