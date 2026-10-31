"""Удаление аниме из избранного."""

from __future__ import annotations

from backend.application.dto.favorite.remove_favorite_command import RemoveFavoriteCommand
from backend.application.interface.repositories.favorite_repository import FavoriteRepository
from backend.application.interface.services import (
    RecommendationServiceInterface,
)
from backend.application.interface.services.profile_overview_cache import (
    ProfileOverviewCacheInterface,
)
from backend.application.interface.unit_of_work import UnitOfWorkInterface


class RemoveFavoriteUseCase:
    """Удаляет аниме из избранного пользователя."""

    def __init__(
        self,
        uow: UnitOfWorkInterface,
        recommendation_service: RecommendationServiceInterface,
        profile_overview_cache: ProfileOverviewCacheInterface,
    ) -> None:
        """Инициализирует сценарий удаления из избранного.

        Args:
            uow: Единица работы, задающая границу транзакции.
            recommendation_service: Сервис рекомендаций, сбрасывается после записи.
            profile_overview_cache: Кэш обзора профиля, сбрасывается после записи.
        """
        self._uow = uow
        self._recommendation_service = recommendation_service
        self._profile_overview_cache = profile_overview_cache

    async def execute(self, command: RemoveFavoriteCommand) -> None:
        """Удаляет аниме из избранного и сбрасывает зависимые кэши.

        Args:
            command: Команда с идентификаторами пользователя и аниме.
        """
        async with self._uow as uow:
            await uow.repository(FavoriteRepository).remove(command.user_id, command.anime_id)
        await self._recommendation_service.invalidate_user(int(command.user_id))
        await self._profile_overview_cache.invalidate_user(
            int(command.user_id),
            include_ai_summary=True,
        )
