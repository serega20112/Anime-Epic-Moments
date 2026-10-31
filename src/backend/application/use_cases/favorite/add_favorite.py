"""Сценарий добавления аниме в избранное."""

import json

from backend.application.dto.favorite.add_favorite_command import AddFavoriteCommand
from backend.application.interface.repositories.favorite_repository import FavoriteRepository
from backend.application.interface.services import (
    RecommendationServiceInterface,
)
from backend.application.interface.services.profile_overview_cache import (
    ProfileOverviewCacheInterface,
)
from backend.application.interface.unit_of_work import UnitOfWorkInterface
from backend.domain import Favorite


class AddFavoriteUseCase:
    """Добавляет аниме в избранное пользователя в рамках транзакции."""

    def __init__(
        self,
        uow: UnitOfWorkInterface,
        recommendation_service: RecommendationServiceInterface,
        profile_overview_cache: ProfileOverviewCacheInterface,
    ) -> None:
        """Инициализирует сценарий добавления в избранное.

        Args:
            uow: Единица работы, задающая границу транзакции.
            recommendation_service: Сервис рекомендаций, сбрасывается после записи.
            profile_overview_cache: Кэш обзора профиля, сбрасывается после записи.
        """
        self._uow = uow
        self._recommendation_service = recommendation_service
        self._profile_overview_cache = profile_overview_cache

    async def execute(self, command: AddFavoriteCommand) -> Favorite:
        """Добавляет аниме в избранное внутри одной транзакции.

        Args:
            command: Команда с идентификаторами пользователя и аниме.

        Returns:
            Favorite: Созданная запись избранного.
        """
        favorite = Favorite(
            user_id=int(command.user_id),
            anime_id=int(command.anime_id),
            title=self._normalize_text(command.title),
            description=self._normalize_text(command.description),
            cover_url=self._normalize_text(command.cover_url),
            genres=self._normalize_genres(command.genres),
            original_title=self._normalize_text(command.original_title),
        )
        async with self._uow as uow:
            saved = await uow.repository(FavoriteRepository).add(favorite)
        await self._recommendation_service.invalidate_user(int(command.user_id))
        await self._profile_overview_cache.invalidate_user(
            int(command.user_id),
            include_ai_summary=True,
        )
        return saved

    def _normalize_text(self, value: str | None) -> str | None:
        """Обрезать текст и вернуть None для пустой строки."""
        text = str(value or "").strip()
        return text or None

    def _normalize_genres(self, value: list[str] | str | None) -> list[str]:
        """Привести жанры к списку без пустых значений."""
        if value is None:
            return []
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        if isinstance(value, str):
            text = value.strip()
            if not text:
                return []
            try:
                parsed = json.loads(text)
            except ValueError:
                parsed = [part.strip() for part in text.split(",")]
            if isinstance(parsed, list):
                return [str(item).strip() for item in parsed if str(item).strip()]
        return []
