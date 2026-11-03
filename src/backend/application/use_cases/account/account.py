"""Сценарии удаления аккаунта и выгрузки данных пользователя.

Удаление опирается на каскады внешних ключей схемы: достаточно снять строку
пользователя, подвластные ему записи убирает база. Выгрузка собирает машиночитаемую
копию профильных разделов одними чтениями, не раскрывая чужих данных.
"""

from __future__ import annotations

from starlette import status

from backend.application.dto.account import DeleteAccountCommand, ExportUserDataQuery
from backend.application.interface.repositories.collection_repository import CollectionRepository
from backend.application.interface.repositories.favorite_repository import FavoriteRepository
from backend.application.interface.repositories.highlight_repository import HighlightRepository
from backend.application.interface.repositories.user_repository import UserRepository
from backend.application.interface.repositories.watch_repository import WatchRepository
from backend.application.interface.services.profile_overview_cache import (
    ProfileOverviewCacheInterface,
)
from backend.application.interface.unit_of_work import UnitOfWorkInterface
from backend.application.use_cases.result import UseCaseResult


class DeleteAccountUseCase:
    """Безвозвратно удаляет аккаунт пользователя вместе со всеми его данными."""

    def __init__(
        self,
        unit_of_work: UnitOfWorkInterface,
        profile_overview_cache: ProfileOverviewCacheInterface,
    ) -> None:
        """Инициализирует сценарий удаления аккаунта.

        Args:
            unit_of_work: Граница транзакции удаления.
            profile_overview_cache: Кэш обзора профиля, сбрасываемый после удаления.
        """
        self._unit_of_work = unit_of_work
        self._profile_overview_cache = profile_overview_cache

    async def execute(self, command: DeleteAccountCommand) -> UseCaseResult:
        """Удалить аккаунт и сбросить его кэш.

        Args:
            command: Идентификатор удаляемого пользователя.

        Returns:
            UseCaseResult: Успех с флагом удаления либо ошибка 404 без пользователя.
        """
        async with self._unit_of_work as uow:
            deleted = await uow.repository(UserRepository).delete(command.user_id)
        if not deleted:
            return UseCaseResult.failure("user_not_found", status_code=status.HTTP_404_NOT_FOUND)
        await self._profile_overview_cache.invalidate_overview(command.user_id)
        return UseCaseResult.success({"deleted": True})


class ExportUserDataUseCase:
    """Собирает машиночитаемую копию данных пользователя."""

    def __init__(self, unit_of_work: UnitOfWorkInterface) -> None:
        """Инициализирует сценарий выгрузки данных.

        Args:
            unit_of_work: Граница транзакции чтения пользовательских разделов.
        """
        self._unit_of_work = unit_of_work

    async def execute(self, query: ExportUserDataQuery) -> UseCaseResult:
        """Собрать профиль, избранное, дневник, хайлайты и коллекции пользователя.

        Args:
            query: Идентификатор пользователя, чьи данные выгружаются.

        Returns:
            UseCaseResult: Словарь разделов выгрузки либо ошибка 404 без пользователя.
        """
        async with self._unit_of_work as uow:
            user = await uow.repository(UserRepository).get_by_id(query.user_id)
            if user is None:
                return UseCaseResult.failure(
                    "user_not_found", status_code=status.HTTP_404_NOT_FOUND
                )
            favorites = await uow.repository(FavoriteRepository).get_by_user(query.user_id)
            statuses = await uow.repository(WatchRepository).get_statuses_by_user(query.user_id)
            highlights = await uow.repository(HighlightRepository).get_by_user(query.user_id)
            collections = await uow.repository(CollectionRepository).get_user_collections(
                query.user_id
            )
        return UseCaseResult.success(
            {
                "profile": {
                    "id": user.id,
                    "email": user.email,
                    "username": user.username,
                    "status": user.status,
                    "created_at": user.created_at.isoformat() if user.created_at else None,
                },
                "favorites": [
                    {"anime_id": favorite.anime_id, "title": favorite.title}
                    for favorite in favorites
                ],
                "statuses": [
                    {
                        "anime_id": status.anime_id,
                        "status": status.status,
                        "current_episode": status.current_episode,
                        "rating": status.rating,
                    }
                    for status in statuses
                ],
                "highlights": [
                    {
                        "id": highlight.id,
                        "anime_id": highlight.anime_id,
                        "episode": highlight.episode,
                        "title": highlight.title,
                    }
                    for highlight in highlights
                ],
                "collections": [
                    {
                        "id": collection.id,
                        "title": collection.title,
                        "is_public": collection.is_public,
                    }
                    for collection in collections
                ],
            }
        )
