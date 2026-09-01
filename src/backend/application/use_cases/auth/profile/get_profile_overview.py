import asyncio
from statistics import mean

from backend.application.interface.repositories.favorite_repository import FavoriteRepository
from backend.application.interface.repositories.highlight_repository import HighlightRepository
from backend.application.interface.repositories.rating_repository import RatingRepository
from backend.application.interface.repositories.user_repository import UserRepository
from backend.application.interface.repositories.watch_repository import WatchRepository
from backend.application.interface.services import AnimeApiClientInterface as AnimeApiClient
from backend.application.interface.services import LLMClientInterface as HuggingFaceLLMClient
from backend.application.interface.services.profile_overview_cache import (
    ProfileOverviewCacheInterface as ProfileOverviewCache,
)
from backend.application.use_cases.highlight.feed.get_liked_highlights import (
    GetLikedHighlightsUseCase,
)
from backend.application.use_cases.highlight.feed.get_saved_highlights import (
    GetSavedHighlightsUseCase,
)
from backend.application.use_cases.highlight.feed.get_user_highlights import (
    GetUserHighlightsUseCase,
)
from backend.domain import (
    ProfileOverview,
    RecentEpisodeCard,
    SmartProfile,
    TopAnimeEntry,
    UserRatingCard,
    ViewingHeatmapCell,
)
from backend.domain.policies.user_profile_policy import (
    build_achievement_badges,
    build_genre_affinities,
    compute_profile_level,
    detect_profile_mood,
)


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
        profile_overview_cache: ProfileOverviewCache | None = None,
        rating_repo: RatingRepository | None = None,
    ):
        self.user_repo = user_repo
        self.highlight_repo = highlight_repo
        self.favorite_repo = favorite_repo
        self.watch_repo = watch_repo
        self.rating_repo = rating_repo
        self.recent_highlights_use_case = GetUserHighlightsUseCase(
            highlight_repo,
            anime_api_client,
            user_repo=user_repo,
        )
        self.liked_highlights_use_case = GetLikedHighlightsUseCase(
            highlight_repo,
            anime_api_client,
            user_repo=user_repo,
        )
        self.saved_highlights_use_case = GetSavedHighlightsUseCase(
            highlight_repo,
            anime_api_client,
            user_repo=user_repo,
        )
        self.anime_api_client = anime_api_client
        self.hf_llm_client = hf_llm_client
        self.profile_overview_cache = profile_overview_cache

    async def execute(self, user_id: int) -> ProfileOverview:
        if self.profile_overview_cache is not None:
            cached_overview = await self.profile_overview_cache.get_overview(user_id)
            if cached_overview is not None:
                return cached_overview

        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError("Пользователь не найден")

        favorites = await self.favorite_repo.get_by_user(user_id)
        own_highlights = await self.highlight_repo.get_by_user(user_id)
        watched_stats = await self.watch_repo.get_watched_anime_stats(user_id=user_id, limit=10)
        heatmap = await self.watch_repo.get_viewing_heatmap(user_id=user_id, days=35)
        recent_sessions = await self.watch_repo.get_recent_viewing_sessions(
            user_id=user_id, limit=10
        )
        ratings = (
            await self.rating_repo.get_by_user(user_id) if self.rating_repo is not None else []
        )
        recent_ratings_anime = {int(item.anime_id) for item in ratings}
        recent_ratings_anime.update(int(item.anime_id) for item in recent_sessions)
        anime_map = await self._load_anime_map(
            favorites=favorites,
            own_highlights=own_highlights,
            watched_stats=watched_stats,
        )
        anime_map = await self._extend_anime_map(anime_map, recent_ratings_anime)
        genre_pool = await self._collect_genres(favorites=favorites, anime_map=anime_map)
        favorite_genres = build_genre_affinities(genre_pool)
        mood = detect_profile_mood(
            genres=genre_pool,
            emotions=[item.emotion or "" for item in own_highlights],
        )
        hours_watched = round(
            sum(item.watched_seconds for item in watched_stats) / 3600,
            1,
        )
        top_anime = await self._build_top_anime(
            favorites=favorites,
            own_highlights=own_highlights,
            watched_stats=watched_stats,
            anime_map=anime_map,
        )
        rating_values = [
            float(item.rating) for item in anime_map.values() if item and item.rating is not None
        ]
        average_rating = round(mean(rating_values), 1) if rating_values else None

        recent_dashboard = await self.recent_highlights_use_case.execute(
            user_id=user_id,
            include_spoilers=True,
            viewer_user_id=user_id,
            sort_by="recent",
        )
        popular_dashboard = await self.recent_highlights_use_case.execute(
            user_id=user_id,
            include_spoilers=True,
            viewer_user_id=user_id,
            sort_by="popular",
        )
        liked_dashboard = await self.liked_highlights_use_case.execute(
            user_id=user_id,
            include_spoilers=True,
            sort_by="popular",
        )
        saved_dashboard = await self.saved_highlights_use_case.execute(
            user_id=user_id,
            include_spoilers=True,
            sort_by="popular",
        )
        summary = await self.highlight_repo.get_profile_summary(user_id)
        recent_activity = await self.highlight_repo.get_recent_activity(user_id, limit=8)
        followers_count, following_count = await self.user_repo.get_follow_stats(user_id)
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
            ai_taste_summary=await self._build_taste_summary(
                user_id=user_id,
                favorite_genres=favorite_genres,
                mood=mood,
                average_rating=average_rating,
                hours_watched=hours_watched,
                top_anime=top_anime,
            ),
        )

        rating_cards = [
            UserRatingCard(
                anime_id=int(item.anime_id),
                title=self._anime_title(anime_map.get(int(item.anime_id)), int(item.anime_id)),
                cover_url=self._anime_cover(anime_map.get(int(item.anime_id))),
                score=item.score,
                rated_at=item.rated_at.strftime("%Y-%m-%d %H:%M"),
            )
            for item in ratings
        ]
        recent_episode_cards = [
            RecentEpisodeCard(
                anime_id=int(item.anime_id),
                title=self._anime_title(anime_map.get(int(item.anime_id)), int(item.anime_id)),
                original_title=self._anime_original_title(anime_map.get(int(item.anime_id))),
                cover_url=self._anime_cover(anime_map.get(int(item.anime_id))),
                episode=int(item.episode),
                updated_at=item.updated_at,
            )
            for item in recent_sessions
        ]
        profile_level = compute_profile_level(
            hours_watched=hours_watched,
            highlight_count=summary.highlight_count,
            likes_received=sum(item.likes_count for item in own_highlights),
            ratings_count=len(ratings),
        )
        overview = ProfileOverview(
            user_id=user.id or user_id,
            email=user.email,
            username=user.username,
            avatar_url=user.avatar_url,
            status=user.status,
            show_watch_activity=user.show_watch_activity,
            show_recent_episodes=user.show_recent_episodes,
            created_at=user.created_at.strftime("%Y-%m-%d"),
            summary=summary,
            recent_highlights=recent_dashboard.items[:4],
            popular_highlights=popular_dashboard.items[:4],
            liked_highlights=liked_dashboard.items[:4],
            saved_highlights=saved_dashboard.items[:4],
            recent_activity=recent_activity,
            recent_episodes=recent_episode_cards,
            profile_level=profile_level,
            ratings=rating_cards,
            smart_profile=smart_profile,
            followers_count=followers_count,
            following_count=following_count,
        )
        if self.profile_overview_cache is not None:
            return await self.profile_overview_cache.set_overview(user_id, overview)
        return overview

    async def _load_anime_map(
        self,
        favorites,
        own_highlights,
        watched_stats,
    ) -> dict[int, object | None]:
        anime_ids = {int(item.anime_id) for item in favorites}
        anime_ids.update(int(item.anime_id) for item in own_highlights)
        anime_ids.update(int(item.anime_id) for item in watched_stats)
        anime_map: dict[int, object | None] = {}
        for anime_id, anime in zip(
            anime_ids,
            await asyncio.gather(
                *(self.anime_api_client.get_by_id(anime_id) for anime_id in anime_ids),
                return_exceptions=True,
            ),
        ):
            anime_map[anime_id] = None if isinstance(anime, BaseException) else anime
        return anime_map

    async def _extend_anime_map(
        self,
        anime_map: dict[int, object | None],
        anime_ids: set[int],
    ) -> dict[int, object | None]:
        """Догружает недостающие аниме из внешнего API в общую карту."""
        missing = {int(anime_id) for anime_id in anime_ids if int(anime_id) not in anime_map}
        if not missing:
            return anime_map
        for anime_id, anime in zip(
            missing,
            await asyncio.gather(
                *(self.anime_api_client.get_by_id(anime_id) for anime_id in missing),
                return_exceptions=True,
            ),
        ):
            anime_map[anime_id] = None if isinstance(anime, BaseException) else anime
        return anime_map

    @staticmethod
    def _anime_title(anime: object | None, anime_id: int) -> str:
        if anime and getattr(anime, "title", None):
            return str(anime.title)
        return f"Anime #{anime_id}"

    @staticmethod
    def _anime_cover(anime: object | None) -> str | None:
        return getattr(anime, "cover_url", None) if anime else None

    @staticmethod
    def _anime_original_title(anime: object | None) -> str | None:
        return getattr(anime, "original_title", None) if anime else None

    async def _collect_genres(self, favorites, anime_map: dict[int, object | None]) -> list[str]:
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

    async def _build_top_anime(
        self, favorites, own_highlights, watched_stats, anime_map
    ) -> list[TopAnimeEntry]:
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

    async def _build_taste_summary(
        self,
        user_id: int,
        favorite_genres,
        mood,
        average_rating: float | None,
        hours_watched: float,
        top_anime,
    ) -> str:
        top_genres = (
            ", ".join(item.name for item in favorite_genres[:3]) or "жанры еще не определились"
        )
        top_titles = ", ".join(item.title for item in top_anime[:3]) or "топ аниме еще не собран"
        fallback = (
            f"{mood.label}: {mood.description} "
            f"Любимые жанры: {top_genres}. "
            f"Средняя оценка профиля: {average_rating if average_rating is not None else 'нет данных'}. "
            f"Зафиксировано {hours_watched} ч. просмотра. "
            f"Топ по активности: {top_titles}."
        )
        if self.profile_overview_cache is not None:
            cached_summary = await self.profile_overview_cache.get_ai_summary(user_id)
            if cached_summary:
                return cached_summary
        if self.hf_llm_client is None:
            return fallback
        summary = await self.hf_llm_client.describe_taste_profile(
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
        if self.profile_overview_cache is not None and summary != fallback:
            await self.profile_overview_cache.set_ai_summary(user_id, summary)
        return summary
