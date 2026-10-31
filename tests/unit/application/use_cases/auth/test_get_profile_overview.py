from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from backend.application.dto import ProfileOverviewQuery
from backend.application.use_cases.auth.profile.get_profile_overview import (
    GetProfileOverviewUseCase,
)
from backend.domain import HighlightProfileSummary, User
from backend.domain.exceptions import NotFoundError
from backend.infrastructure.cache.key_value_store import KeyValueStore
from backend.infrastructure.cache.profile_overview_cache import ProfileOverviewCache
from tests.support.fakes import FakeUnitOfWork


def _user() -> User:
    """Собрать пользователя профиля с аватаром и датами."""
    return User(
        id=4,
        email="user@example.com",
        username="tester",
        password_hash="hashed",
        avatar_url="https://example.com/avatar.png",
        created_at=datetime(2026, 3, 20),
    )


def _anime_card() -> SimpleNamespace:
    """Собрать карточку тайтла из каталога для расчёта вкусов."""
    return SimpleNamespace(
        title="Gintama",
        original_title="Gintama Kyuu",
        cover_url="https://example.com/gintama.jpg",
        description="Описание тайтла",
        year=2011,
        rating=8.9,
        genres=["Comedy", "Action"],
        episode_count=12,
        external_id="123",
    )


def _dashboard(items: list[str]) -> SimpleNamespace:
    """Собрать дашборд хайлайтов с указанными карточками."""
    return SimpleNamespace(items=items)


def _use_case(
    *,
    user=None,
    watch_seconds: float = 7200.0,
    ai_summary: str = "Тебя тянет к экшен-комедиям.",
) -> tuple:
    """Собрать сценарий обзора профиля со всеми двойниками зависимостей."""
    user_repository = AsyncMock()
    user_repository.get_by_id.return_value = user
    user_repository.get_follow_stats.return_value = (11, 6)
    favorite_repository = AsyncMock()
    favorite_repository.get_by_user.return_value = [
        SimpleNamespace(anime_id=7, genres=["Comedy", "Action"])
    ]
    highlight_repository = AsyncMock()
    highlight_repository.get_by_user.return_value = [
        SimpleNamespace(anime_id=7, likes_count=9, emotion="funny")
    ]
    highlight_repository.get_profile_summary.return_value = HighlightProfileSummary(
        highlight_count=3, like_count=5, saved_count=7
    )
    highlight_repository.get_recent_activity.return_value = [SimpleNamespace(action="like")]
    watch_repository = AsyncMock()
    watch_repository.get_watched_anime_stats.return_value = [
        SimpleNamespace(anime_id=7, watched_seconds=watch_seconds)
    ]
    watch_repository.get_viewing_heatmap.return_value = [
        SimpleNamespace(date="2026-03-28", interactions=3)
    ]
    watch_repository.get_recent_viewing_sessions.return_value = [
        SimpleNamespace(anime_id=7, episode=2, updated_at=datetime(2026, 3, 28, 19, 0))
    ]
    rating_repository = AsyncMock()
    rating_repository.get_by_user.return_value = []
    anime_api_client = AsyncMock()
    anime_api_client.get_by_id.return_value = _anime_card()
    llm_client = AsyncMock()
    llm_client.describe_taste_profile.return_value = ai_summary
    profile_cache = AsyncMock()
    profile_cache.get_overview.return_value = None
    profile_cache.get_ai_summary.return_value = None
    profile_cache.set_overview.side_effect = lambda _user_id, overview: overview
    recent_highlights = AsyncMock()
    recent_highlights.execute.return_value = _dashboard(["recent-1", "recent-2", "recent-3"])
    liked_highlights = AsyncMock()
    liked_highlights.execute.return_value = _dashboard(["liked-1"])
    saved_highlights = AsyncMock()
    saved_highlights.execute.return_value = _dashboard(["saved-1"])
    uow = FakeUnitOfWork(
        UserRepository=user_repository,
        FavoriteRepository=favorite_repository,
        HighlightRepository=highlight_repository,
        WatchRepository=watch_repository,
        RatingRepository=rating_repository,
    )
    use_case = GetProfileOverviewUseCase(
        uow,
        anime_api_client,
        llm_client,
        profile_cache,
        recent_highlights,
        liked_highlights,
        saved_highlights,
    )
    return (
        use_case,
        uow,
        user_repository,
        rating_repository,
        recent_highlights,
        liked_highlights,
        saved_highlights,
        profile_cache,
    )


@pytest.mark.unit
class TestGetProfileOverviewUseCase:
    """Юнит-тесты сборки обзора профиля пользователя."""

    async def test_builds_profile_sections_and_caches_overview(self):
        """Что тестируем: полный обзор профиля с подборками и социой активностью.
        Что передаём: существующего пользователя со всеми связанными срезами данных.
        Что ожидаем: секции собраны, счётчики верны, обзор записан в кэш.
        """
        use_case, uow, users, _ratings, recent, liked, saved, cache = _use_case(user=_user())

        overview = await use_case.execute(ProfileOverviewQuery(user_id=4))

        assert uow.commits == 1
        users.get_by_id.assert_awaited_once_with(4)
        assert overview.summary.saved_count == 7
        assert overview.username == "tester"
        assert overview.created_at == "2026-03-20"
        assert overview.recent_highlights == ["recent-1", "recent-2", "recent-3"]
        assert overview.liked_highlights == ["liked-1"]
        assert overview.saved_highlights == ["saved-1"]
        assert overview.recent_activity[0].action == "like"
        assert overview.followers_count == 11
        assert overview.following_count == 6
        assert overview.ratings == []
        assert overview.recent_episodes[0].episode == 2
        assert overview.recent_episodes[0].title == "Gintama"
        assert overview.smart_profile.hours_watched == 2.0
        assert overview.smart_profile.top_anime[0].title == "Gintama"
        assert overview.smart_profile.favorite_genres[0].name == "Comedy"
        assert overview.smart_profile.ai_taste_summary == "Тебя тянет к экшен-комедиям."
        assert overview.profile_level.xp > 0
        assert overview.profile_level.level >= 1
        cache.set_overview.assert_awaited_once_with(4, overview)
        assert recent.execute.await_count == 2
        assert liked.execute.await_count == 1
        assert saved.execute.await_count == 1

    async def test_builds_dashboard_queries_for_owner_and_viewer(self):
        """Что тестируем: персональные запросы к дашбордам хайлайтов.
        Что передаём: пользователя с сохранёнными и лайкнутыми подборками.
        Что ожидаем: дашборды вызваны с автором, зрителем и включёнными спойлерами.
        """
        use_case, _uow, _users, _ratings, recent, liked, saved, _cache = _use_case(user=_user())

        await use_case.execute(ProfileOverviewQuery(user_id=4))

        recent_query = recent.execute.await_args_list[0].args[0]
        popular_query = recent.execute.await_args_list[1].args[0]
        assert recent_query.user_id == 4
        assert recent_query.viewer_user_id == 4
        assert recent_query.include_spoilers is True
        assert recent_query.sort_by == "recent"
        assert popular_query.sort_by == "popular"
        assert liked.execute.await_args.args[0].sort_by == "popular"
        assert saved.execute.await_args.args[0].user_id == 4

    async def test_returns_cached_overview_without_repositories(self):
        """Что тестируем: отдачу обзора из кэша без обращений к базе.
        Что передаём: кэш возвращает готовый обзор.
        Что ожидаем: тот же объект, сценарии дашбордов не вызываются.
        """
        use_case, _uow, users, _ratings, recent, _liked, _saved, cache = _use_case(user=_user())
        cached = SimpleNamespace(username="from-cache")
        cache.get_overview.return_value = cached

        overview = await use_case.execute(ProfileOverviewQuery(user_id=4))

        assert overview is cached
        users.get_by_id.assert_not_awaited()
        recent.execute.assert_not_awaited()

    async def test_reuses_cached_ai_summary(self):
        """Что тестируем: переиспользование AI-резюме из кэша.
        Что передаём: кэш отдает сохранённое резюме вкуса.
        Что ожидаем: LLM не вызывается, резюме взято из кэша.
        """
        use_case, _uow, _users, _ratings, _recent, _liked, _saved, cache = _use_case(user=_user())
        cache.get_ai_summary.return_value = "Кэшируемое резюме."
        llm_client = AsyncMock()
        use_case._hf_llm_client = llm_client

        overview = await use_case.execute(ProfileOverviewQuery(user_id=4))

        assert overview.smart_profile.ai_taste_summary == "Кэшируемое резюме."
        llm_client.describe_taste_profile.assert_not_awaited()

    async def test_stores_generated_ai_summary_for_future_calls(self):
        """Что тестируем: сохранение сгенерированного резюме в кэш.
        Что передаём: LLM возвращает текст, отличный от запасного.
        Что ожидаем: резюме записано в кэш по идентификатору пользователя.
        """
        use_case, _uow, _users, _ratings, _recent, _liked, _saved, cache = _use_case(
            user=_user(), ai_summary="Свежее резюме."
        )

        await use_case.execute(ProfileOverviewQuery(user_id=4))

        cache.set_ai_summary.assert_awaited_once_with(4, "Свежее резюме.")

    async def test_raises_not_found_for_unknown_user(self):
        """Что тестируем: отказ при отсутствии пользователя.
        Что передаём: репозиторий возвращает None.
        Что ожидаем: NotFoundError, кэш не записывается.
        """
        use_case, _uow, _users, _ratings, _recent, _liked, _saved, cache = _use_case()

        with pytest.raises(NotFoundError):
            await use_case.execute(ProfileOverviewQuery(user_id=404))

        cache.set_overview.assert_not_awaited()

    async def test_caches_real_overview_between_calls(self):
        """Что тестируем: сквозное кеширование обзора в реальном хранилище.
        Что передаём: кэш поверх in-memory хранилища ключ-значение.
        Что ожидаем: второй вызов возвращает кэшированный обзор без чтения базы.
        """
        use_case, _uow, users, *_rest = _use_case(user=_user())
        use_case._profile_overview_cache = ProfileOverviewCache(
            store=KeyValueStore(redis_url=None, namespace="test-profile-overview"),
            overview_ttl_seconds=180,
            ai_summary_ttl_seconds=1800,
        )

        first = await use_case.execute(ProfileOverviewQuery(user_id=4))
        users.get_by_id.reset_mock()
        second = await use_case.execute(ProfileOverviewQuery(user_id=4))

        assert first.username == "tester"
        assert second.username == "tester"
        users.get_by_id.assert_not_awaited()
