from statistics import mean

from src.backend.domain.user.policy import (
    build_achievement_badges,
    build_genre_affinities,
    detect_profile_mood,
)
from src.backend.domain.user.value_object import ProfileOverview
from src.backend.domain.user.value_object import SmartProfile, TopAnimeEntry, ViewingHeatmapCell
from src.backend.infrastructure.external.anime_api_client import AnimeApiClient
from src.backend.infrastructure.external.huggingface_llm_client import HuggingFaceLLMClient
from src.backend.repository.favorite_repository import FavoriteRepository
from src.backend.repository.highlight_repository import HighlightRepository
from src.backend.repository.user_repository import UserRepository
from src.backend.repository.watch_repository import WatchRepository
from src.backend.use_case.highlight.get_liked_highlights import GetLikedHighlightsUseCase
from src.backend.use_case.highlight.get_saved_highlights import GetSavedHighlightsUseCase
from src.backend.use_case.highlight.get_user_highlights import GetUserHighlightsUseCase


class GetProfileOverviewUseCase:
    """Собирает профиль пользователя с social-статистикой и быстрыми подборками."""

    def __init__(
        self,
        user_repo: UserRepository,
        highlight_repo: HighlightRepository,
        anime_api_client: AnimeApiClient,
        favorite_repo: FavoriteRepository,
        watch_repo: WatchRepository,
        hf_llm_client: HuggingFaceLLMClient | None = None,
    ):
        self.user_repo = user_repo
        self.highlight_repo = highlight_repo
        self.favorite_repo = favorite_repo
        self.watch_repo = watch_repo
        self.recent_highlights_use_case = GetUserHighlightsUseCase(
            highlight_repo,
            anime_api_client,
        )
        self.liked_highlights_use_case = GetLikedHighlightsUseCase(
            highlight_repo,
            anime_api_client,
        )
        self.saved_highlights_use_case = GetSavedHighlightsUseCase(
            highlight_repo,
            anime_api_client,
        )
        self.anime_api_client = anime_api_client
        self.hf_llm_client = hf_llm_client

    def execute(self, user_id: int) -> ProfileOverview:
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError("Пользователь не найден")

        favorites = self.favorite_repo.get_by_user(user_id)
        own_highlights = self.highlight_repo.get_by_user(user_id)
        watched_stats = self.watch_repo.get_watched_anime_stats(user_id=user_id, limit=10)
        heatmap = self.watch_repo.get_viewing_heatmap(user_id=user_id, days=35)
        anime_map = self._load_anime_map(
            favorites=favorites,
            own_highlights=own_highlights,
            watched_stats=watched_stats,
        )
        genre_pool = self._collect_genres(favorites=favorites, anime_map=anime_map)
        favorite_genres = build_genre_affinities(genre_pool)
        mood = detect_profile_mood(
            genres=genre_pool,
            emotions=[item.emotion or "" for item in own_highlights],
        )
        hours_watched = round(
            sum(item.watched_seconds for item in watched_stats) / 3600,
            1,
        )
        top_anime = self._build_top_anime(
            favorites=favorites,
            own_highlights=own_highlights,
            watched_stats=watched_stats,
            anime_map=anime_map,
        )
        rating_values = [
            float(item.rating)
            for item in anime_map.values()
            if item and item.rating is not None
        ]
        average_rating = round(mean(rating_values), 1) if rating_values else None

        recent_dashboard = self.recent_highlights_use_case.execute(
            user_id=user_id,
            include_spoilers=True,
            viewer_user_id=user_id,
            sort_by="recent",
        )
        popular_dashboard = self.recent_highlights_use_case.execute(
            user_id=user_id,
            include_spoilers=True,
            viewer_user_id=user_id,
            sort_by="popular",
        )
        liked_dashboard = self.liked_highlights_use_case.execute(
            user_id=user_id,
            include_spoilers=True,
            sort_by="popular",
        )
        saved_dashboard = self.saved_highlights_use_case.execute(
            user_id=user_id,
            include_spoilers=True,
            sort_by="popular",
        )
        summary = self.highlight_repo.get_profile_summary(user_id)
        recent_activity = self.highlight_repo.get_recent_activity(user_id, limit=8)
        smart_profile = SmartProfile(
            favorite_genres=favorite_genres,
            dominant_mood=mood,
            average_rating=average_rating,
            hours_watched=hours_watched,
            top_anime=top_anime,
            heatmap=[
                ViewingHeatmapCell(date=item.date, interactions=item.interactions)
                for item in heatmap
            ],
            achievements=build_achievement_badges(
                profile_summary=summary,
                hours_watched=hours_watched,
                favorite_genres=favorite_genres,
                highlight_likes_received=sum(item.likes_count for item in own_highlights),
                top_mood=mood,
            ),
            ai_taste_summary=self._build_taste_summary(
                favorite_genres=favorite_genres,
                mood=mood,
                average_rating=average_rating,
                hours_watched=hours_watched,
                top_anime=top_anime,
            ),
        )

        return ProfileOverview(
            user_id=user.id or user_id,
            email=user.email,
            username=user.username,
            avatar_url=user.avatar_url,
            created_at=user.created_at.strftime("%Y-%m-%d"),
            summary=summary,
            recent_highlights=recent_dashboard.items[:4],
            popular_highlights=popular_dashboard.items[:4],
            liked_highlights=liked_dashboard.items[:4],
            saved_highlights=saved_dashboard.items[:4],
            recent_activity=recent_activity,
            smart_profile=smart_profile,
        )

    def _load_anime_map(self, favorites, own_highlights, watched_stats) -> dict[int, object | None]:
        anime_ids = {
            int(item.anime_id)
            for item in favorites
        }
        anime_ids.update(int(item.anime_id) for item in own_highlights)
        anime_ids.update(int(item.anime_id) for item in watched_stats)
        anime_map: dict[int, object | None] = {}
        for anime_id in anime_ids:
            anime_map[anime_id] = self.anime_api_client.get_by_id(anime_id)
        return anime_map

    def _collect_genres(self, favorites, anime_map: dict[int, object | None]) -> list[str]:
        genres: list[str] = []
        for favorite in favorites:
            if favorite.genres:
                genres.extend(favorite.genres)
                continue
            anime = anime_map.get(int(favorite.anime_id))
            if anime and getattr(anime, "genres", None):
                genres.extend(anime.genres)
        for anime in anime_map.values():
            if anime and getattr(anime, "genres", None):
                genres.extend(anime.genres)
        return genres

    def _build_top_anime(self, favorites, own_highlights, watched_stats, anime_map) -> list[TopAnimeEntry]:
        weights: dict[int, float] = {}
        for item in watched_stats:
            weights[item.anime_id] = weights.get(item.anime_id, 0.0) + (item.watched_seconds / 600)
        for item in favorites:
            anime_id = int(item.anime_id)
            weights[anime_id] = weights.get(anime_id, 0.0) + 8.0
        for item in own_highlights:
            anime_id = int(item.anime_id)
            weights[anime_id] = weights.get(anime_id, 0.0) + 3.0

        ranked = sorted(weights.items(), key=lambda value: value[1], reverse=True)
        result: list[TopAnimeEntry] = []
        for anime_id, weight in ranked[:5]:
            anime = anime_map.get(anime_id)
            result.append(
                TopAnimeEntry(
                    anime_id=anime_id,
                    title=(
                        anime.title
                        if anime and getattr(anime, "title", None)
                        else f"Anime #{anime_id}"
                    ),
                    cover_url=anime.cover_url if anime else None,
                    rating=anime.rating if anime else None,
                    weight=round(float(weight), 1),
                )
            )
        return result

    def _build_taste_summary(
        self,
        favorite_genres,
        mood,
        average_rating: float | None,
        hours_watched: float,
        top_anime,
    ) -> str:
        top_genres = ", ".join(item.name for item in favorite_genres[:3]) or "жанры еще не определились"
        top_titles = ", ".join(item.title for item in top_anime[:3]) or "топ аниме еще не собран"
        fallback = (
            f"{mood.label}: {mood.description} "
            f"Любимые жанры: {top_genres}. "
            f"Средняя оценка профиля: {average_rating if average_rating is not None else 'нет данных'}. "
            f"Зафиксировано {hours_watched} ч. просмотра. "
            f"Топ по активности: {top_titles}."
        )
        if self.hf_llm_client is None:
            return fallback
        return self.hf_llm_client.describe_taste_profile(
            profile_data={
                "mood": mood.label,
                "mood_description": mood.description,
                "favorite_genres": [item.name for item in favorite_genres[:5]],
                "average_rating": average_rating,
                "hours_watched": hours_watched,
                "top_titles": [item.title for item in top_anime[:5]],
            },
            fallback=fallback,
        )
