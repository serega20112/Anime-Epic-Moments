"""User use case providers."""

from __future__ import annotations

from dishka import Provider, Scope, provide

from backend.application.use_cases import GetPublicProfileOverviewUseCase, SetUserFollowUseCase
from backend.application.use_cases.auth.get_profile_overview import GetProfileOverviewUseCase
from backend.domain.unit_of_work import UnitOfWorkInterface
from backend.infrastructure.cache.profile_overview_cache import ProfileOverviewCache
from backend.infrastructure.repositories.collection_repository import CollectionRepository
from backend.infrastructure.repositories.user_repository import UserRepository


class UserUseCaseProvider(Provider):
    """Provide user and public profile use cases."""

    @provide(scope=Scope.REQUEST)
    def set_user_follow(
        self,
        user_repository: UserRepository,
        profile_overview_cache: ProfileOverviewCache,
        unit_of_work: UnitOfWorkInterface,
    ) -> SetUserFollowUseCase:
        """Provide the set user follow use case.

        Args:
            user_repository: User repository.
            profile_overview_cache: Profile overview cache.
            unit_of_work: Transaction boundary.

        Returns:
            SetUserFollowUseCase: Configured use case.
        """
        return SetUserFollowUseCase(user_repository, profile_overview_cache, unit_of_work)

    @provide(scope=Scope.REQUEST)
    def get_public_profile_overview(
        self,
        get_profile_overview: GetProfileOverviewUseCase,
        user_repository: UserRepository,
        collection_repository: CollectionRepository,
    ) -> GetPublicProfileOverviewUseCase:
        """Provide the get public profile overview use case.

        Args:
            get_profile_overview: Profile overview use case.
            user_repository: User repository.
            collection_repository: Collection repository.

        Returns:
            GetPublicProfileOverviewUseCase: Configured use case.
        """
        return GetPublicProfileOverviewUseCase(
            get_profile_overview,
            user_repository,
            collection_repository,
        )
