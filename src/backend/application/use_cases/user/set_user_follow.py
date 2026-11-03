"""Сценарий подписки и отписки от пользователя."""

from __future__ import annotations

from starlette import status

from backend.application.dto import SetUserFollowCommand
from backend.application.interface.repositories.notification_repository import (
    NotificationRepository,
)
from backend.application.interface.repositories.user_repository import UserRepository
from backend.application.interface.services.profile_overview_cache import (
    ProfileOverviewCacheInterface,
)
from backend.application.interface.unit_of_work import UnitOfWorkInterface
from backend.application.use_cases.result import UseCaseResult
from backend.domain import Notification
from backend.domain.entities.notification.notification import KIND_NEW_FOLLOWER
from backend.domain.policies.notification_policy import notification_text


class SetUserFollowUseCase:
    """Создаёт или удаляет подписку между пользователями."""

    def __init__(
        self,
        unit_of_work: UnitOfWorkInterface,
        profile_overview_cache: ProfileOverviewCacheInterface,
    ) -> None:
        """Инициализирует сценарий подписки на пользователя.

        Args:
            unit_of_work: Граница транзакции изменения подписки.
            profile_overview_cache: Кэш обзоров профиля обеих сторон.
        """
        self._unit_of_work = unit_of_work
        self._profile_overview_cache = profile_overview_cache

    async def execute(self, command: SetUserFollowCommand) -> UseCaseResult:
        """Создаёт или удаляет подписку внутри транзакции.

        Args:
            command: Команда подписки с идентификаторами сторон и флагом.

        Returns:
            UseCaseResult: Результат операции подписки.
        """
        async with self._unit_of_work as uow:
            repository = uow.repository(UserRepository)
            target_user = await repository.get_by_id(command.followed_user_id)
            if target_user is None:
                return UseCaseResult.failure(
                    "Пользователь для подписки не найден", status_code=status.HTTP_404_NOT_FOUND
                )
            if command.follow:
                result = await repository.follow(command.follower_user_id, command.followed_user_id)
            else:
                result = await repository.unfollow(
                    command.follower_user_id, command.followed_user_id
                )
            await self._notify_followed(uow, command, result)

        await self._profile_overview_cache.invalidate_overview(int(command.follower_user_id))
        await self._profile_overview_cache.invalidate_overview(int(command.followed_user_id))
        return UseCaseResult.success(result)

    @staticmethod
    async def _notify_followed(uow: UnitOfWorkInterface, command, result) -> None:
        """Записать уведомление новому подписчику, если подписка реально создана.

        Отписка, собственная подписка на себя и повтор (ничего не изменилось)
        уведомления не создают.

        Args:
            uow: Граница транзакции с доступом к репозиторию уведомлений.
            command: Команда подписки с идентификаторами сторон.
            result: Результат операции подписки.
        """
        if not command.follow or not result:
            return
        if int(command.follower_user_id) == int(command.followed_user_id):
            return
        await uow.repository(NotificationRepository).add(
            Notification(
                user_id=int(command.followed_user_id),
                kind=KIND_NEW_FOLLOWER,
                text=notification_text(KIND_NEW_FOLLOWER),
                actor_user_id=int(command.follower_user_id),
            )
        )
