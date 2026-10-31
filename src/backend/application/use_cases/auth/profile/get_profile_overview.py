"""Сценарий сборки обзора профиля пользователя."""

from __future__ import annotations

import asyncio
from collections.abc import Iterable
from dataclasses import dataclass, replace

from backend.application.dto import HighlightDashboardQuery, ProfileOverviewQuery
from backend.application.interface.repositories.favorite_repository import FavoriteRepository
from backend.application.interface.repositories.highlight_repository import HighlightRepository
from backend.application.interface.repositories.rating_repository import RatingRepository
from backend.application.interface.repositories.user_repository import UserRepository
from backend.application.interface.repositories.watch_repository import WatchRepository
from backend.application.interface.services import AnimeApiClientInterface, LLMClientInterface
from backend.application.interface.services.profile_overview_cache import (
    ProfileOverviewCacheInterface,
)
from backend.application.interface.unit_of_work import UnitOfWorkInterface
from backend.application.use_cases.auth.profile.profile_cards import (
    AnimeCard,
    average_catalog_rating,
    build_rating_cards,
    build_recent_episode_cards,
    build_top_anime,
    collect_genres,
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
    Favorite,
    Highlight,
    HighlightActivityItem,
    HighlightDashboard,
    HighlightProfileSummary,
    ProfileOverview,
    SmartProfile,
    TopAnimeEntry,
    User,
    UserAnimeRating,
    ViewingHeatmapCell,
    ViewingSession,
)
from backend.domain.exceptions import NotFoundError
from backend.domain.policies.user_profile_policy import (
    build_achievement_badges,
    build_genre_affinities,
    compute_hours_watched,
    compute_profile_level,
    detect_profile_mood,
    rank_top_anime,
)
from backend.domain.value_objects.user.smart_profile import GenreAffinity, ProfileMoodInsight
from backend.domain.value_objects.watch.page_data import WatchedAnimeStat

PROFILE_CARDS_LIMIT = 4
WATCHED_STATS_LIMIT = 10
HEATMAP_DAYS = 35
RECENT_SESSIONS_LIMIT = 10
RECENT_ACTIVITY_LIMIT = 8
TOP_ANIME_LIMIT = 5
PREVIEW_LIMIT = 3
ANIME_FETCH_CONCURRENCY = 12


@dataclass(frozen=True, slots=True)
class _ProfileState:
    """Данные профиля, прочитанные из базы за одну транзакцию.

    Attributes:
        user: Агрегат пользователя.
        favorites: Избранные тайтлы пользователя.
        own_highlights: Хайлайты, созданные пользователем.
        watched_stats: Агрегированная статистика просмотра по тайтлам.
        heatmap: Тепловая карта активности просмотра по дням.
        recent_sessions: Последние сессии просмотра.
        ratings: Оценки пользователя по тайтлам.
        summary: Счётчики хайлайтов, лайков и сохранений.
        recent_activity: Последние реакции сообщества на хайлайты.
        followers_count: Число подписчиков пользователя.
        following_count: Число подписок пользователя.
    """

    user: User
    favorites: list[Favorite]
    own_highlights: list[Highlight]
    watched_stats: list[WatchedAnimeStat]
    heatmap: list[ViewingHeatmapCell]
    recent_sessions: list[ViewingSession]
    ratings: list[UserAnimeRating]
    summary: HighlightProfileSummary
    recent_activity: list[HighlightActivityItem]
    followers_count: int
    following_count: int


class GetProfileOverviewUseCase:
    """Собирает обзор профиля пользователя с social-статистикой и подборками."""

    def __init__(
        self,
        unit_of_work: UnitOfWorkInterface,
        anime_api_client: AnimeApiClientInterface,
        hf_llm_client: LLMClientInterface,
        profile_overview_cache: ProfileOverviewCacheInterface,
        recent_highlights_use_case: GetUserHighlightsUseCase,
        liked_highlights_use_case: GetLikedHighlightsUseCase,
        saved_highlights_use_case: GetSavedHighlightsUseCase,
    ) -> None:
        """Собрать сценарий обзора профиля.

        Args:
            unit_of_work: Граница транзакции чтения данных профиля.
            anime_api_client: Клиент каталога для карточек тайтлов.
            hf_llm_client: Клиент LLM для текстового резюме вкуса.
            profile_overview_cache: Кэш обзора профиля и AI-резюме.
            recent_highlights_use_case: Сценарий дашборда хайлайтов автора.
            liked_highlights_use_case: Сценарий дашборда лайкнутых хайлайтов.
            saved_highlights_use_case: Сценарий дашборда сохранённых хайлайтов.
        """
        self._unit_of_work = unit_of_work
        self._anime_api_client = anime_api_client
        self._hf_llm_client = hf_llm_client
        self._profile_overview_cache = profile_overview_cache
        self._recent_highlights_use_case = recent_highlights_use_case
        self._liked_highlights_use_case = liked_highlights_use_case
        self._saved_highlights_use_case = saved_highlights_use_case

    async def execute(self, query: ProfileOverviewQuery) -> ProfileOverview:
        """Собрать обзор профиля: избранное, статистику и вкусы.

        Локальные данные читаются одной транзакцией до обращений к каталогу и
        LLM, чтобы соединение с базой не удерживалось время сетевых вызовов.

        Args:
            query: Идентификатор пользователя, чей профиль собирается.

        Returns:
            ProfileOverview: Готовый обзор профиля.

        Raises:
            NotFoundError: Если пользователь с таким идентификатором отсутствует.
        """
        cached_overview = await self._profile_overview_cache.get_overview(query.user_id)
        if cached_overview is not None:
            return cached_overview

        state = await self._load_state(query.user_id)
        anime_map = await self._load_anime_map(state)
        genre_pool = collect_genres(state.favorites, anime_map)
        favorite_genres = build_genre_affinities(genre_pool)
        mood = detect_profile_mood(
            genres=genre_pool,
            emotions=[item.emotion or "" for item in state.own_highlights],
        )
        hours_watched = compute_hours_watched(state.watched_stats)
        top_anime = build_top_anime(
            rank_top_anime(
                watched_stats=state.watched_stats,
                favorites=state.favorites,
                own_highlights=state.own_highlights,
                limit=TOP_ANIME_LIMIT,
            ),
            anime_map,
        )
        likes_received = self._likes_received(state.own_highlights)
        recent, popular, liked, saved = await self._load_dashboards(query.user_id)

        smart_profile = SmartProfile(
            favorite_genres=favorite_genres,
            dominant_mood=mood,
            average_rating=average_catalog_rating(anime_map),
            hours_watched=hours_watched,
            top_anime=top_anime,
            heatmap=list(state.heatmap),
            achievements=build_achievement_badges(
                profile_summary=state.summary,
                hours_watched=hours_watched,
                favorite_genres=favorite_genres,
                highlight_likes_received=likes_received,
                top_mood=mood,
            ),
            ai_taste_summary=await self._build_taste_summary(
                user_id=query.user_id,
                favorite_genres=favorite_genres,
                mood=mood,
                average_rating=average_catalog_rating(anime_map),
                hours_watched=hours_watched,
                top_anime=top_anime,
            ),
        )
        overview = ProfileOverview(
            user_id=state.user.id or query.user_id,
            email=state.user.email,
            username=state.user.username,
            avatar_url=state.user.avatar_url,
            status=state.user.status,
            show_watch_activity=state.user.show_watch_activity,
            show_recent_episodes=state.user.show_recent_episodes,
            created_at=state.user.created_at.strftime("%Y-%m-%d"),
            summary=state.summary,
            recent_highlights=recent.items[:PROFILE_CARDS_LIMIT],
            popular_highlights=popular.items[:PROFILE_CARDS_LIMIT],
            liked_highlights=liked.items[:PROFILE_CARDS_LIMIT],
            saved_highlights=saved.items[:PROFILE_CARDS_LIMIT],
            recent_activity=state.recent_activity,
            recent_episodes=build_recent_episode_cards(state.recent_sessions, anime_map),
            profile_level=compute_profile_level(
                hours_watched=hours_watched,
                highlight_count=state.summary.highlight_count,
                likes_received=likes_received,
                ratings_count=len(state.ratings),
            ),
            ratings=build_rating_cards(state.ratings, anime_map),
            smart_profile=smart_profile,
            followers_count=state.followers_count,
            following_count=state.following_count,
        )
        return await self._profile_overview_cache.set_overview(query.user_id, overview)

    async def _load_state(self, user_id: int) -> _ProfileState:
        """Прочитать данные профиля одной транзакцией.

        Args:
            user_id: Идентификатор пользователя.

        Returns:
            _ProfileState: Собранные для профиля срезы данных.

        Raises:
            NotFoundError: Если пользователь с таким идентификатором отсутствует.
        """
        async with self._unit_of_work as uow:
            user_repository = uow.repository(UserRepository)
            watch_repository = uow.repository(WatchRepository)
            highlight_repository = uow.repository(HighlightRepository)
            user = await user_repository.get_by_id(user_id)
            if user is None:
                raise NotFoundError("Пользователь не найден")
            followers_count, following_count = await user_repository.get_follow_stats(user_id)
            return _ProfileState(
                user=user,
                favorites=await uow.repository(FavoriteRepository).get_by_user(user_id),
                own_highlights=await highlight_repository.get_by_user(user_id),
                watched_stats=await watch_repository.get_watched_anime_stats(
                    user_id=user_id, limit=WATCHED_STATS_LIMIT
                ),
                heatmap=[
                    ViewingHeatmapCell(date=item.date, interactions=item.interactions)
                    for item in await watch_repository.get_viewing_heatmap(
                        user_id=user_id, days=HEATMAP_DAYS
                    )
                ],
                recent_sessions=await watch_repository.get_recent_viewing_sessions(
                    user_id=user_id, limit=RECENT_SESSIONS_LIMIT
                ),
                ratings=await uow.repository(RatingRepository).get_by_user(user_id),
                summary=await highlight_repository.get_profile_summary(user_id),
                recent_activity=await highlight_repository.get_recent_activity(
                    user_id, limit=RECENT_ACTIVITY_LIMIT
                ),
                followers_count=followers_count,
                following_count=following_count,
            )

    async def _load_dashboards(self, user_id: int) -> tuple[HighlightDashboard, ...]:
        """Собрать четыре дашборда хайлайтов профиля.

        Вызовы идут последовательно: все дашборды читают одну и ту же сессию
        базы, а параллельные запросы к одному соединению SQLAlchemy запрещены.

        Args:
            user_id: Идентификатор автора хайлайтов.

        Returns:
            tuple[HighlightDashboard, ...]: Дашборды recent, popular, liked, saved.
        """
        personal = HighlightDashboardQuery(
            user_id=user_id,
            viewer_user_id=user_id,
            include_spoilers=True,
        )
        recent = await self._recent_highlights_use_case.execute(replace(personal, sort_by="recent"))
        popular = await self._recent_highlights_use_case.execute(
            replace(personal, sort_by="popular")
        )
        liked = await self._liked_highlights_use_case.execute(replace(personal, sort_by="popular"))
        saved = await self._saved_highlights_use_case.execute(replace(personal, sort_by="popular"))
        return recent, popular, liked, saved

    async def _load_anime_map(self, state: _ProfileState) -> dict[int, AnimeCard]:
        """Подгрузить карточки аниме для всех тайтлов профиля.

        Запросы идут параллельно, но под семафором: профиль давнего пользователя
        включает сотни тайтлов, а непросанированный gather ставил бы столько же
        одновременных запросов к каталогу и добывал таймауты вместо карточек.

        Args:
            state: Прочитанные из базы данные профиля.

        Returns:
            dict[int, AnimeCard]: Карточки тайтлов по идентификатору; None при сбое.
        """
        anime_ids = {int(item.anime_id) for item in state.favorites}
        anime_ids.update(int(item.anime_id) for item in state.own_highlights)
        anime_ids.update(int(item.anime_id) for item in state.watched_stats)
        anime_ids.update(int(item.anime_id) for item in state.ratings)
        anime_ids.update(int(item.anime_id) for item in state.recent_sessions)
        if not anime_ids:
            return {}
        semaphore = asyncio.Semaphore(ANIME_FETCH_CONCURRENCY)

        async def fetch(anime_id: int) -> AnimeCard:
            """Получить одну карточку тайтла под лимитом одновременных запросов."""
            async with semaphore:
                return await self._anime_api_client.get_by_id(anime_id)

        loaded = await asyncio.gather(
            *(fetch(anime_id) for anime_id in anime_ids),
            return_exceptions=True,
        )
        return {
            anime_id: None if isinstance(anime, BaseException) else anime
            for anime_id, anime in zip(anime_ids, loaded, strict=True)
        }

    async def _build_taste_summary(
        self,
        user_id: int,
        favorite_genres: Iterable[GenreAffinity],
        mood: ProfileMoodInsight,
        average_rating: float | None,
        hours_watched: float,
        top_anime: Iterable[TopAnimeEntry],
    ) -> str:
        """Собрать текстовое описание вкусов пользователя.

        Args:
            user_id: Идентификатор пользователя.
            favorite_genres: Любимые жанры с числом вхождений.
            mood: Определённый настрой профиля.
            average_rating: Средняя оценка тайтлов из каталога.
            hours_watched: Накопленные часы просмотра.
            top_anime: Заметные тайтлы пользователя.

        Returns:
            str: Текст резюме вкуса — из кэша, от LLM или запасной формулировки.
        """
        cached_summary = await self._profile_overview_cache.get_ai_summary(user_id)
        if cached_summary:
            return cached_summary
        genres = list(favorite_genres)
        titles = list(top_anime)
        top_genres = ", ".join(item.name for item in genres[:PREVIEW_LIMIT])
        top_titles = ", ".join(item.title for item in titles[:PREVIEW_LIMIT])
        fallback = (
            f"{mood.label}: {mood.description} "
            f"Любимые жанры: {top_genres or 'жанры еще не определились'}. "
            f"Средняя оценка профиля: "
            f"{average_rating if average_rating is not None else 'нет данных'}. "
            f"Зафиксировано {hours_watched} ч. просмотра. "
            f"Топ по активности: {top_titles or 'топ аниме еще не собран'}."
        )
        summary = await self._hf_llm_client.describe_taste_profile(
            profile_data={
                "mood": mood.label,
                "mood_description": mood.description,
                "favorite_genres": [item.name for item in genres[:TOP_ANIME_LIMIT]],
                "average_rating": average_rating,
                "hours_watched": hours_watched,
                "top_titles": [item.title for item in titles[:TOP_ANIME_LIMIT]],
            },
            fallback=fallback,
        )
        if summary != fallback:
            await self._profile_overview_cache.set_ai_summary(user_id, summary)
        return summary

    @staticmethod
    def _likes_received(highlights: Iterable[Highlight]) -> int:
        """Суммировать лайки, полученные хайлайтами пользователя.

        Args:
            highlights: Хайлайты автора.

        Returns:
            int: Общее число лайков на хайлайтах.
        """
        return sum(item.likes_count for item in highlights)
