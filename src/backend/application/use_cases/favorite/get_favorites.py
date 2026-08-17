from backend.domain import FavoriteRepository
from backend.domain.favorite.value_object import FavoriteAnimeCard
from backend.domain.services import AnimeApiClientInterface as AnimeApiClient


class GetFavoritesUseCase:
    def __init__(self, repo: FavoriteRepository, anime_api_client: AnimeApiClient):
        self.repo = repo
        self.anime_api_client = anime_api_client

    async def execute(self, user_id: int) -> list[FavoriteAnimeCard]:
        favorites = await self.repo.get_by_user(user_id)
        result: list[FavoriteAnimeCard] = []
        for favorite in favorites:
            anime = None
            needs_remote_lookup = not favorite.title
            if needs_remote_lookup:
                anime = await self.anime_api_client.get_by_id(favorite.anime_id)
            watch_id = await self._resolve_watch_id(
                stored_anime_id=favorite.anime_id,
                resolved_external_id=anime.external_id if anime else None,
            )
            title = favorite.title or (
                anime.title if anime and anime.title else f"Anime #{favorite.anime_id}"
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
                )
            )
        return result

    async def _resolve_watch_id(self, stored_anime_id: int, resolved_external_id: str | None) -> int:
        """Выбирает id для построения watch-ссылки."""
        try:
            numeric_id = int(str(resolved_external_id or "").strip())
            return numeric_id if numeric_id > 0 else int(stored_anime_id)
        except (TypeError, ValueError):
            return int(stored_anime_id)
