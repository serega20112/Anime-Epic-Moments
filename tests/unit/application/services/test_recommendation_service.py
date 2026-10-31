from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from backend.application.services.recommendation_service import RecommendationService
from backend.infrastructure.cache import RecommendationCache
from tests.support.fakes import FakeUnitOfWork


def _service(
    cache: RecommendationCache,
    *,
    favorites: list[object] | None = None,
    highlights: list[object] | None = None,
    top_anime: list[object] | None = None,
) -> tuple[RecommendationService, FakeUnitOfWork, AsyncMock, AsyncMock, Mock]:
    """Собрать сервис рекомендаций поверх двойников репозиториев и каталога.

    Args:
        cache: Настоящий in-memory кэш подборок.
        favorites: Ответ репозитория избранного.
        highlights: Ответ репозитория хайлайтов.
        top_anime: Ответ клиента каталога на запрос топа.

    Returns:
        tuple: Сервис, граница транзакции, двойники избранного, хайлайтов
        и клиента каталога.
    """
    favorite_repo = AsyncMock()
    favorite_repo.get_by_user.return_value = favorites if favorites is not None else []
    highlight_repo = AsyncMock()
    highlight_repo.get_by_user.return_value = highlights if highlights is not None else []
    anime_client = Mock()
    anime_client.get_by_id = AsyncMock(return_value=None)
    anime_client.get_top_anime = AsyncMock(return_value=top_anime if top_anime is not None else [])
    anime_client.search_by_title = AsyncMock(return_value=[])
    service = RecommendationService(anime_client, cache)
    uow = FakeUnitOfWork(
        FavoriteRepository=favorite_repo,
        HighlightRepository=highlight_repo,
    )
    return service, uow, favorite_repo, highlight_repo, anime_client


@pytest.mark.unit
class TestRecommendationService:
    """Юнит-тесты сервиса генерации рекомендаций."""

    async def test_returns_cached_items_without_hitting_repositories(self):
        """Что тестируем: cache hit не запускает репозитории и внешние API заново.
        Что передаём: пользователя с ранее закэшированными рекомендациями.
        Что ожидаем: возвращается кэш, а репозитории/клиент не вызываются.
        """
        cache = RecommendationCache(ttl_seconds=60)
        cached_item = SimpleNamespace(anime_id=7, title="Cached")
        await cache.set(user_id=1, limit=5, value=[cached_item])
        service, uow, favorite_repo, _highlight_repo, anime_client = _service(cache)

        result = await service.generate(uow, user_id=1, limit=5)

        assert result == [cached_item]
        favorite_repo.get_by_user.assert_not_called()
        anime_client.get_top_anime.assert_not_called()

    @pytest.mark.parametrize(
        ("force_refresh", "expected_calls"),
        [(False, 0), (True, 1)],
    )
    async def test_respects_force_refresh(
        self, force_refresh, expected_calls, anime_factory
    ) -> None:
        """Что тестируем: force_refresh обходит кэш и пересчитывает рекомендации.
        Что передаём: force_refresh=True/False при наличии кэша.
        Что ожидаем: при force_refresh перезапрос топ-аниме и свежий результат, иначе кэш.
        """
        cache = RecommendationCache(ttl_seconds=60)
        cached_item = SimpleNamespace(anime_id=9, title="Cached")
        await cache.set(user_id=1, limit=3, value=[cached_item])
        service, uow, _favorite_repo, _highlight_repo, anime_client = _service(
            cache,
            favorites=[SimpleNamespace(anime_id=555, genres=["Action"])],
            top_anime=[anime_factory(external_id="101", title="Fresh")],
        )

        result = await service.generate(uow, user_id=1, limit=3, force_refresh=force_refresh)

        assert anime_client.get_top_anime.await_count == expected_calls
        if force_refresh:
            assert result[0].title == "Fresh"
        else:
            assert result == [cached_item]

    async def test_caches_empty_result(self):
        """Что тестируем: пустой результат кэшируется и не пересчитывается повторно.
        Что передаём: пользователя без избранного и хайлайтов.
        Что ожидаем: репозитории вызываются один раз, возвращается пустой список.
        """
        cache = RecommendationCache(ttl_seconds=60)
        service, uow, favorite_repo, _highlight_repo, _anime_client = _service(cache)

        first = await service.generate(uow, user_id=2, limit=5)
        second = await service.generate(uow, user_id=2, limit=5)

        assert first == []
        assert second == []
        favorite_repo.get_by_user.assert_called_once_with(2)

    async def test_reads_through_provided_unit_of_work(self):
        """Что тестируем: чтение вкуса идёт в транзакции вызывающего сценария.
        Что передаём: единицу работы с двойниками репозиториев.
        Что ожидаем: сервис не держит собственных репозиториев, а берёт их из uow.
        """
        cache = RecommendationCache(ttl_seconds=60)
        service, uow, _favorite_repo, _highlight_repo, _anime_client = _service(cache)

        await service.generate(uow, user_id=4, limit=5, force_refresh=True)

        assert not hasattr(service, "fav_repo")
        assert not hasattr(service, "highlight_repo")

    async def test_excludes_favorites_from_recommendations(self, anime_factory):
        """Что тестируем: избранный тайтл не возвращается как рекомендация.
        Что передаём: избранник с external_id и топ из такого же тайтла.
        Что ожидаем: подборка пуста — кандидат исключён по external_id.
        """
        cache = RecommendationCache(ttl_seconds=60)
        service, uow, _favorite_repo, _highlight_repo, _anime_client = _service(
            cache,
            favorites=[SimpleNamespace(anime_id=101, genres=["Action"])],
            top_anime=[anime_factory(external_id="101", title="Naruto", genres=["Action"])],
        )

        result = await service.generate(uow, user_id=8, limit=5, force_refresh=True)

        assert [item.anime_id for item in result] == []

    async def test_invalidate_user_clears_cached_entries(self):
        """Что тестируем: invalidate_user удаляет сохраненный результат пользователя.
        Что передаём: пользователя с закэшированными рекомендациями.
        Что ожидаем: после invalidate кэш для этого пользователя пуст.
        """
        cache = RecommendationCache(ttl_seconds=60)
        await cache.set(user_id=3, limit=5, value=[SimpleNamespace(anime_id=3)])
        service, _uow, _favorite_repo, _highlight_repo, _anime_client = _service(cache)

        await service.invalidate_user(3)

        assert await cache.get(user_id=3, limit=5) is None
