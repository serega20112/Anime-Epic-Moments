"""Сценарий выставления оценки аниме."""

from __future__ import annotations

from backend.application.dto.rating.set_user_anime_rating_command import (
    SetUserAnimeRatingCommand,
)
from backend.application.interface.repositories.rating_repository import RatingRepository
from backend.application.interface.services.profile_overview_cache import (
    ProfileOverviewCacheInterface,
)
from backend.application.interface.unit_of_work import UnitOfWorkInterface
from backend.domain import UserAnimeRating


class SetUserAnimeRatingUseCase:
    """Выставляет или обновляет оценку пользователя по аниме."""

    def __init__(
        self,
        uow: UnitOfWorkInterface,
        profile_overview_cache: ProfileOverviewCacheInterface,
    ) -> None:
        """Собрать сценарий выставления оценки.

        Args:
            uow: Единица работы, задающая границу транзакции.
            profile_overview_cache: Кэш обзора профиля, сбрасывается после записи.
        """
        self._uow = uow
        self._profile_overview_cache = profile_overview_cache

    async def execute(self, command: SetUserAnimeRatingCommand) -> UserAnimeRating:
        """Сохранить оценку в границах одной транзакции.

        Args:
            command: Команда с оценкой пользователя.

        Returns:
            UserAnimeRating: Сохранённая оценка.
        """
        rating = UserAnimeRating(
            user_id=command.user_id,
            anime_id=command.anime_id,
            score=command.score,
        )
        async with self._uow as uow:
            saved = await uow.repository(RatingRepository).upsert(rating)
        await self._profile_overview_cache.invalidate_overview(int(command.user_id))
        return saved
