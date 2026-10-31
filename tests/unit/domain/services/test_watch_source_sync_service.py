from __future__ import annotations

import inspect

from backend.application.interface.services.watch_source_service import (
    WatchSourceSyncServiceInterface,
)
from backend.application.services.watch_source_service import WatchSourceSyncService
from backend.domain.entities.anime.anime import Anime, has_adult_genres


class TestWatchSourceSyncServiceInterface:
    """Тесты контракта порта сервиса синхронизации источников."""

    def test_abstract_method_names(self):
        """Что тестируем: порт описывает методы, которыми реально пользуются сценарии.
        Что передаём: набор абстрактных методов порта.
        Что ожидаем: в порте есть синхронизация, проверка включённости провайдера
        и карта доступности — без «методов-призраков», которых у реализации нет.
        """
        assert {
            "sync_for_anime",
            "is_enabled",
            "get_enabled_provider_names",
            "get_provider_label",
            "get_translations_availability",
        } == set(WatchSourceSyncServiceInterface.__abstractmethods__)

    def test_implementation_covers_every_port_method(self):
        """Что тестируем: реализация не шире и не уже порта.
        Что передаём: каждый абстрактный метод порта.
        Что ожидаем: у сервиса есть метод с тем же набором параметров — иначе
        подмена реализации даст AttributeError или TypeError в рантайме.
        """
        for method_name in WatchSourceSyncServiceInterface.__abstractmethods__:
            port_method = getattr(WatchSourceSyncServiceInterface, method_name)
            implementation = getattr(WatchSourceSyncService, method_name, None)
            assert implementation is not None, method_name
            assert list(inspect.signature(port_method).parameters) == list(
                inspect.signature(implementation).parameters
            )

    def test_cannot_be_instantiated(self):
        """Что тестируем: порт нельзя инстанцировать напрямую.
        Что передаём: попытку создать экземпляр абстрактного класса.
        Что ожидаем: TypeError.
        """
        try:
            WatchSourceSyncServiceInterface()  # type: ignore[abstract]
            raised = False
        except TypeError:
            raised = True
        assert raised is True

    def test_service_does_not_own_a_repository(self):
        """Что тестируем: сервис не держит собственный репозиторий.
        Что передаём: конструктор сервиса.
        Что ожидаем: границы транзакции приходят параметром sync_for_anime, а не
        полем сервиса — иначе запись осталась бы незафиксированной.
        """
        parameters = list(inspect.signature(WatchSourceSyncService.__init__).parameters)

        assert "watch_repo" not in parameters
        assert "unit_of_work" in inspect.signature(WatchSourceSyncService.sync_for_anime).parameters


class _FakeProvider:
    """Провайдер с одним значимым для маршрутизации именем."""

    def __init__(self, name: str):
        """Создать провайдера с указанным именем."""
        self.provider_name = name


class TestHentaiRouting:
    """Тесты маршрутизации взрослого контента на профильные провайдеры."""

    def test_is_adult_detects_hentai_genres(self):
        """Что тестируем: признание тайтла взрослым по жанрам.
        Что передаём: списки жанров с hentai, ecchi и без них.
        Что ожидаем: правило живёт в домене и срабатывает только на 18+-жанры.
        """
        assert has_adult_genres(["Action", "Hentai"]) is True
        assert has_adult_genres(["Ecchi"]) is True
        assert has_adult_genres(["Adventure", "Fantasy"]) is False
        assert has_adult_genres(None) is False
        assert has_adult_genres([]) is False

    def test_anime_entity_exposes_adult_flag(self):
        """Что тестируем: взрослый контент определяется самой сущностью Anime.
        Что передаём: тайтл с жанром Hentai и тайтл без него.
        Что ожидаем: свойство is_adult отражает доменное правило.
        """
        assert Anime(external_id="1", title="Bible Black", genres=["Hentai"]).is_adult is True
        assert Anime(external_id="2", title="Gintama", genres=["Action"]).is_adult is False

    def test_filtered_providers_adult_keeps_only_hentai_sources(self):
        """Что тестируем: список провайдеров для взрослого контента.
        Что передаём: смешанный список провайдеров.
        Что ожидаем: остаются только профильные источники. Kodik сознательно
        исключён: хентай-тайтлы лежат там под не-озвучками и засоряют выдачу.
        """
        service = WatchSourceSyncService.__new__(WatchSourceSyncService)
        service.providers = [
            _FakeProvider("Kodik"),
            _FakeProvider("Eporner"),
            _FakeProvider("Hentaigasm"),
            _FakeProvider("Hanime"),
            _FakeProvider("YouTube"),
        ]

        adult = [provider.provider_name for provider in service._filtered_providers(True)]

        assert adult == ["Eporner", "Hentaigasm", "Hanime"]

    def test_filtered_providers_normal_keeps_all(self):
        """Что тестируем: список провайдеров для обычного контента.
        Что передаём: два провайдера, один из них профильный для 18+.
        Что ожидаем: опрашивается весь список.
        """
        service = WatchSourceSyncService.__new__(WatchSourceSyncService)
        service.providers = [_FakeProvider("Kodik"), _FakeProvider("Eporner")]

        names = [provider.provider_name for provider in service._filtered_providers(False)]

        assert names == ["Kodik", "Eporner"]
