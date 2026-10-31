from __future__ import annotations

import inspect

from backend.application.interface.services.anime_api_client import AnimeApiClientInterface
from backend.infrastructure.external.catalog.anime_api_client import AnimeApiClient


class TestAnimeApiClientInterface:
    """Тесты контракта порта клиента каталога аниме."""

    def test_is_abstract(self):
        """Что тестируем: порт остаётся абстрактным описанием.
        Что передаём: атрибут абстрактных методов.
        Что ожидаем: это frozenset имён, а не обычный набор полей.
        """
        assert isinstance(AnimeApiClientInterface.__abstractmethods__, frozenset)

    def test_abstract_method_names(self):
        """Что тестируем: порт описывает методы, которые вызывают сценарии.
        Что передаём: набор абстрактных методов порта.
        Что ожидаем: поиск по названию и описанию, топ, сезон, карточка и
        фильтрованный каталог — без «методов-призраков» вроде search.
        """
        assert {
            "get_by_id",
            "search_by_title",
            "search_by_description",
            "get_top_anime",
            "get_season_popular",
            "filter_catalog",
        } == set(AnimeApiClientInterface.__abstractmethods__)

    def test_cannot_be_instantiated(self):
        """Что тестируем: порт нельзя создать напрямую.
        Что передаём: попытку инстанцировать абстрактный класс.
        Что ожидаем: TypeError.
        """
        try:
            AnimeApiClientInterface()  # type: ignore[abstract]
            raised = False
        except TypeError:
            raised = True
        assert raised is True

    def test_implementation_covers_every_port_method(self):
        """Что тестируем: клиент каталога реализует порт целиком и так же по параметрам.
        Что передаём: каждый абстрактный метод порта.
        Что ожидаем: у клиента есть метод с тем же набором параметров.
        """
        for method_name in AnimeApiClientInterface.__abstractmethods__:
            port_method = getattr(AnimeApiClientInterface, method_name)
            implementation = getattr(AnimeApiClient, method_name, None)
            assert implementation is not None, method_name
            assert list(inspect.signature(port_method).parameters) == list(
                inspect.signature(implementation).parameters
            )
