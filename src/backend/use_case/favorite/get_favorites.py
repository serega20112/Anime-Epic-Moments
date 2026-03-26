from typing import List
from src.backend.domain.favorite.value_object import FavoriteAnimeCard
from src.backend.infrastructure.external.anime_api_client import AnimeApiClient
from src.backend.repository.favorite_repository import FavoriteRepository


class GetFavoritesUseCase:
    def __init__(self, repo: FavoriteRepository, anime_api_client: AnimeApiClient):
        self.repo = repo
        self.anime_api_client = anime_api_client

    def execute(self, user_id: int) -> List[FavoriteAnimeCard]:
        favorites = self.repo.get_by_user(user_id)
        result: List[FavoriteAnimeCard] = []
        for favorite in favorites:
            anime = self.anime_api_client.get_by_id(favorite.anime_id)
            title = anime.title if anime and anime.title else f"Anime #{favorite.anime_id}"
            result.append(
                FavoriteAnimeCard(
                    anime_id=favorite.anime_id,
                    title=title,
                    description=anime.description if anime and anime.description else "Описание недоступно",
                    cover_url=anime.cover_url if anime else None,
                    genres=anime.genres if anime and anime.genres else [],
                    watch_url=f"/watch/{favorite.anime_id}?episode=1",
                    added_at=favorite.added_at.strftime("%Y-%m-%d"),
                )
            )
        return result
