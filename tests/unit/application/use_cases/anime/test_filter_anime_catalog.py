from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from backend.application.dto.anime import AnimeCatalogResult, FilterAnimeCatalogQuery
from backend.application.use_cases.anime.filter_anime_catalog import (
    DEFAULT_PER_PAGE,
    WINDOW_LIMIT,
    FilterAnimeCatalogUseCase,
)
from backend.domain.value_objects.anime.catalog_page import CatalogPage
from backend.domain.value_objects.anime.genre_filter import GenreMatchMode
from tests.support.fakes import FakeUnitOfWork


def anime(external_id: str, title: str, genres: list[str], year: int = 2020) -> object:
    """Собрать сущность аниме для ответов фейкового провайдера.

    Args:
        external_id: Внешний идентификатор, числовой для локальных поисков.
        title: Название тайтла.
        genres: Список жанров.
        year: Год выхода.

    Returns:
        object: Сущность ``Anime`` с переданными полями.
    """
    from backend.domain.entities.anime.anime import Anime

    return Anime(
        external_id=external_id,
        title=title,
        genres=genres,
        year=year,
    )


def use_case(
    items: list[object],
    translations: dict[int, list[object]] | None = None,
    availability: dict[str, bool] | None = None,
) -> tuple[FilterAnimeCatalogUseCase, AsyncMock, AsyncMock, AsyncMock]:
    """Собрать сценарий с фейковыми зависимостями.

    Args:
        items: Тайтлы, которые вернёт провайдер в окне.
        translations: Локальные озвучки по идентификатору аниме.
        availability: Результат обращения к карте доступности провайдера.

    Returns:
        tuple[FilterAnimeCatalogUseCase, AsyncMock, AsyncMock, AsyncMock]:
            Сценарий и его фейковые зависимости: клиент, watch-репозиторий
            и сервис синхронизации источников.
    """
    api_client = AsyncMock()
    api_client.filter_catalog.return_value = CatalogPage(
        items=tuple(items),
        page=1,
        per_page=len(items),
        total=len(items),
    )
    watch_repository = AsyncMock()
    watch_repository.get_translations.side_effect = lambda anime_id: (translations or {}).get(
        anime_id, []
    )
    sync_service = AsyncMock()
    sync_service.get_translations_availability.side_effect = lambda **kwargs: (
        [object()] * (1 if (availability or {}).get(str(kwargs.get("title")), False) else 0)
    )
    uow = FakeUnitOfWork(WatchRepository=watch_repository)
    return (
        FilterAnimeCatalogUseCase(uow, api_client, sync_service),
        api_client,
        watch_repository,
        sync_service,
    )


@pytest.mark.unit
class TestFilterAnimeCatalogUseCase:
    """Юнит-тесты фильтрации каталога аниме."""

    async def test_accepts_positional_dependencies(self):
        """Что тестируем: сборку сценария позиционными зависимостями DI.
        Что передаём: границу транзакции, клиент каталога и сервис синхронизации.
        Что ожидаем: страница каталога собрана; регрессия — потеря параметра
        сервиса роняла роут каталога с TypeError.
        """
        target, _api_client, _watch_repository, _sync_service = use_case(
            [anime("1", "A", ["Action"])]
        )

        result = await target.execute(FilterAnimeCatalogQuery(genre_mode=GenreMatchMode.ANY))

        assert [item.title for item in result.items] == ["A"]

    async def test_any_mode_serves_requested_page(self):
        """Что тестируем: страницу провайдера при режиме «любой жанр».
        Что передаём: запрос с genre_mode=ANY и двумя тайтлами.
        Что ожидаем: провайдер вызван с запрошенной страницей, лишний жанр
        отсечён локально, total точный.
        """
        items = [anime("1", "A", ["Action"]), anime("2", "B", ["Comedy"])]
        target, api_client, _, _ = use_case(items)

        result = await target.execute(
            FilterAnimeCatalogQuery(genres=("Action",), genre_mode=GenreMatchMode.ANY)
        )

        assert isinstance(result, AnimeCatalogResult)
        assert [item.title for item in result.items] == ["A"]
        kwargs = api_client.filter_catalog.await_args.kwargs
        assert kwargs["page"] == 1
        assert kwargs["per_page"] == DEFAULT_PER_PAGE
        assert result.total_is_exact is True

    async def test_all_mode_scans_window_and_keeps_intersection(self):
        """Что тестируем: режим «все жанры» через расширенное окно провайдера.
        Что передаём: запрос ALL на второй странице с per_page=10.
        Что ожидаем: провайдер вызван одной страницей с удлинённым окном,
        остаются только тайтлы с обоими жанрами.
        """
        items = [
            anime("1", "A", ["Action", "Comedy"]),
            anime("2", "B", ["Action"]),
            anime("3", "C", ["Comedy", "Action"]),
        ]
        target, api_client, _, _ = use_case(items)

        result = await target.execute(
            FilterAnimeCatalogQuery(
                genres=("Action", "Comedy"),
                genre_mode=GenreMatchMode.ALL,
                page=2,
                per_page=10,
            )
        )

        kwargs = api_client.filter_catalog.await_args.kwargs
        assert kwargs["page"] == 1
        assert kwargs["per_page"] == min(WINDOW_LIMIT, 2 * 10)
        assert [item.title for item in result.items] == []
        assert result.total == 2

    async def test_has_dub_keeps_only_titles_with_translation(self):
        """Что тестируем: фильтр «только с озвучкой».
        Что передаём: у одного тайтла локальная озвучка есть, у другого нет,
            и провайдер его тоже не считает озвученным.
        Что ожидаем: в результат попал только первый тайтл.
        """
        items = [anime("7", "Dubbed", ["Action"]), anime("8", "Raw", ["Action"])]
        target, _, watch_repository, _ = use_case(
            items,
            translations={7: [object()]},
            availability={"Dubbed": True, "Raw": False},
        )

        result = await target.execute(
            FilterAnimeCatalogQuery(has_dub=True, genre_mode=GenreMatchMode.ANY)
        )

        assert [item.title for item in result.items] == ["Dubbed"]
        watch_repository.get_translations.assert_awaited_with(anime_id=8)

    async def test_facets_count_all_scanned_titles(self):
        """Что тестируем: расчёт фасетов жанров.
        Что передаём: окно из трёх тайтлов с пересекающимися жанрами.
        Что ожидаем: фасеты посчитаны по всему окну, а не по отфильтрованной
        странице, и отсортированы по убыванию количества. Регрессия: раньше
        уже встреченный жанр пропускался, и каждый фасет показывал count=1.
        """
        items = [
            anime("1", "A", ["Action", "Comedy"]),
            anime("2", "B", ["Action"]),
            anime("3", "C", ["Drama"]),
        ]
        target, _, _, _ = use_case(items)

        result = await target.execute(
            FilterAnimeCatalogQuery(genres=("Comedy",), genre_mode=GenreMatchMode.ANY)
        )

        facets = {facet.name: facet.count for facet in result.genre_facets}
        assert facets["Action"] == 2
        assert facets["Comedy"] == 1
        assert result.items[0].title == "A"

    async def test_adult_titles_hidden_by_default(self):
        """Что тестируем: выдачу каталога без явного согласия на 18+.
        Что передаём: обычный тайтл и тайтл с жанром hentai.
        Что ожидаем: взрослый тайтл исключён, ordinary остался.
        """
        items = [anime("1", "Safe", ["Action"]), anime("2", "Adult", ["Hentai"])]
        target, _, _, _ = use_case(items)

        result = await target.execute(
            FilterAnimeCatalogQuery(genre_mode=GenreMatchMode.ANY, include_adult=False)
        )

        assert [item.title for item in result.items] == ["Safe"]

    async def test_adult_titles_included_when_requested(self):
        """Что тестируем: выдачу каталога с явным include_adult.
        Что передаём: те же два тайтла и включённый флаг взрослого контента.
        Что ожидаем: оба тайтла в выдаче.
        """
        items = [anime("1", "Safe", ["Action"]), anime("2", "Adult", ["Hentai"])]
        target, _, _, _ = use_case(items)

        result = await target.execute(
            FilterAnimeCatalogQuery(genre_mode=GenreMatchMode.ANY, include_adult=True)
        )

        assert [item.title for item in result.items] == ["Safe", "Adult"]
