"""Список избранного пользователя."""

from __future__ import annotations

from backend.application.dto.favorite.get_favorites_query import GetFavoritesQuery
from backend.application.interface.repositories.favorite_repository import FavoriteRepository
from backend.application.interface.services import AnimeApiClientInterface
from backend.application.interface.unit_of_work import UnitOfWorkInterface
from backend.domain.value_objects.favorite.favorite_card import FavoriteAnimeCard


class GetFavoritesUseCase:
    """Возвращает карточки избранного пользователя."""

    def __init__(
        self,
        uow: UnitOfWorkInterface,
        anime_api_client: AnimeApiClientInterface,
    ) -> None:
        """Инициализирует сценарий получения избранного.

        Args:
            uow: Единица работы, через которую берётся репозиторий.
            anime_api_client: Клиент API аниме для дополнения данных.
        """
        self._uow = uow
        self._anime_api_client = anime_api_client

    async def execute(self, query: GetFavoritesQuery) -> list[FavoriteAnimeCard]:
        """Собирает карточки избранного, дополняя их данными каталога.

        Args:
            query: Запрос с идентификатором пользователя.

        Returns:
            list[FavoriteAnimeCard]: Карточки аниме в порядке добавления.
        """
        async with self._uow as uow:
            favorites = await uow.repository(FavoriteRepository).get_by_user(query.user_id)
        result: list[FavoriteAnimeCard] = []
        for favorite in favorites:
            anime = None
            if not favorite.title:
                anime = await self._anime_api_client.get_by_id(favorite.anime_id)
            watch_id = self._resolve_watch_id(
                stored_anime_id=favorite.anime_id,
                resolved_external_id=anime.external_id if anime else None,
            )
            title = favorite.title or (
                anime.title if anime and anime.title else f"Anime #{favorite.anime_id}"
            )
            original_title = favorite.original_title or (
                anime.original_title if anime and anime.original_title else None
            )
            result.append(
                FavoriteAnimeCard(
                    anime_id=favorite.anime_id,
                    title=title,
                    description=(
                        favorite.description
                        or (
                            anime.description
                            if anime and anime.description
                            else "Описание недоступно"
                        )
                    ),
                    cover_url=favorite.cover_url or (anime.cover_url if anime else None),
                    genres=favorite.genres or (anime.genres if anime and anime.genres else []),
                    watch_url=f"/watch/{watch_id}?episode=1",
                    added_at=favorite.added_at.strftime("%Y-%m-%d"),
                    original_title=original_title,
                )
            )
        return result

    def _resolve_watch_id(self, stored_anime_id: int, resolved_external_id: str | None) -> int:
        """Выбирает идентификатор для построения watch-ссылки.

        Args:
            stored_anime_id: Хранимый идентификатор аниме.
            resolved_external_id: Внешний идентификатор от API.

        Returns:
            int: Идентификатор для watch-ссылки.
        """
        try:
            numeric_id = int(str(resolved_external_id or "").strip())
            return numeric_id if numeric_id > 0 else int(stored_anime_id)
        except (TypeError, ValueError):
            return int(stored_anime_id)
