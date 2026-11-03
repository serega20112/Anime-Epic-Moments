"""Провайдеры сценариев профилей и подписок."""

from __future__ import annotations

from dishka import Provider, Scope, provide

from backend.application.interface.unit_of_work import UnitOfWorkInterface
from backend.application.use_cases import GetPublicProfileOverviewUseCase, SetUserFollowUseCase
from backend.application.use_cases.account.account import (
    DeleteAccountUseCase,
    ExportUserDataUseCase,
)
from backend.application.use_cases.auth.profile.get_profile_overview import (
    GetProfileOverviewUseCase,
)
from backend.infrastructure.cache.profile_overview_cache import ProfileOverviewCache


class UserUseCaseProvider(Provider):
    """Провайдер сценариев пользователя и публичных профилей."""

    @provide(scope=Scope.REQUEST)
    async def set_user_follow(
        self,
        unit_of_work: UnitOfWorkInterface,
        profile_overview_cache: ProfileOverviewCache,
    ) -> SetUserFollowUseCase:
        """Создать сценарий подписки и отписки."""
        return SetUserFollowUseCase(unit_of_work, profile_overview_cache)

    @provide(scope=Scope.REQUEST)
    async def get_public_profile_overview(
        self,
        unit_of_work: UnitOfWorkInterface,
        get_profile_overview: GetProfileOverviewUseCase,
    ) -> GetPublicProfileOverviewUseCase:
        """Создать сценарий обзора публичного профиля."""
        return GetPublicProfileOverviewUseCase(unit_of_work, get_profile_overview)

    @provide(scope=Scope.REQUEST)
    async def delete_account(
        self,
        unit_of_work: UnitOfWorkInterface,
        profile_overview_cache: ProfileOverviewCache,
    ) -> DeleteAccountUseCase:
        """Создать сценарий удаления аккаунта."""
        return DeleteAccountUseCase(unit_of_work, profile_overview_cache)

    @provide(scope=Scope.REQUEST)
    async def export_user_data(self, unit_of_work: UnitOfWorkInterface) -> ExportUserDataUseCase:
        """Создать сценарий выгрузки данных пользователя."""
        return ExportUserDataUseCase(unit_of_work)
