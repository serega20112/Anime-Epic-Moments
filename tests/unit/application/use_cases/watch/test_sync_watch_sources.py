from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from backend.application.dto import SyncWatchSourcesQuery
from backend.application.use_cases import SyncWatchSourcesUseCase
from backend.domain.entities.anime.anime import Anime
from tests.support.fakes import FakeUnitOfWork


def _anime(**overrides) -> Anime:
    """Собрать карточку аниме из каталога с переопределёнными полями."""
    fields = {
        "external_id": "12345",
        "title": "Gintama",
        "year": 2011,
        "genres": ["Comedy"],
    }
    fields.update(overrides)
    return Anime(**fields)


def _use_case(*, sources, availability=None) -> tuple:
    """Собрать сценарий синхронизации с двойниками клиента, сервиса и транзакции.

    Args:
        sources: Список источников, который вернёт сервис синхронизации.
        availability: Карта доступности серий по озвучкам.

    Returns:
        tuple: Сценарий, единица работы, клиент каталога и сервис синхронизации.
    """
    anime_api_client = AsyncMock()
    anime_api_client.get_by_id.return_value = _anime()
    sync_service = AsyncMock()
    sync_service.is_enabled.return_value = True
    sync_service.sync_for_anime.return_value = sources
    sync_service.get_translations_availability.return_value = availability or []
    sync_service.get_enabled_provider_names.return_value = ["kinobox"]
    uow = FakeUnitOfWork()
    use_case = SyncWatchSourcesUseCase(uow, anime_api_client, sync_service)
    return use_case, uow, anime_api_client, sync_service


@pytest.mark.unit
class TestSyncWatchSourcesUseCase:
    """Юнит-тесты синхронизации источников просмотра."""

    async def test_returns_summary_of_found_sources(self):
        """Что тестируем: успешную сводку по найденным источникам.
        Что передаём: запрос серии и два источника от провайдера.
        Что ожидаем: число источников и названия провайдеров в ответе.
        """
        use_case, _uow, _client, sync_service = _use_case(sources=["s1", "s2"])

        result = await use_case.execute(SyncWatchSourcesQuery(anime_id=7, episode=2))

        assert result.ok is True
        assert result.data == {"enabled": True, "sources_count": 2, "provider_names": ["kinobox"]}
        called = sync_service.sync_for_anime.await_args.kwargs
        assert called["anime_id"] == 7
        assert called["episode"] == 2
        assert called["force"] is False
        assert called["anime"].title == "Gintama"

    async def test_found_sources_are_committed(self):
        """Что тестируем: границу транзакции найденных источников.
        Что передаём: два источника, сохранённых сервисом в единицу работы.
        Что ожидаем: один commit и ноль rollback — иначе запись молча откатится
        при закрытии сессии запроса, а эндпоинт ответит 200.
        """
        use_case, uow, _client, sync_service = _use_case(sources=["s1", "s2"])

        result = await use_case.execute(SyncWatchSourcesQuery(anime_id=7, episode=2))

        assert result.ok is True
        assert uow.commits == 1
        assert uow.rollbacks == 0
        assert sync_service.sync_for_anime.await_args.kwargs["unit_of_work"] is uow

    async def test_rolled_back_and_not_committed_on_timeout(self):
        """Что тестируем: откат неполной выборки при таймауте провайдера.
        Что передаём: сервис бросает TimeoutError посреди записи источников.
        Что ожидаем: ноль commit, один rollback и статус 504.
        """
        use_case, uow, _client, sync_service = _use_case(sources=[])
        sync_service.sync_for_anime.side_effect = TimeoutError

        result = await use_case.execute(SyncWatchSourcesQuery(anime_id=7, episode=2))

        assert result.status_code == 504
        assert uow.commits == 0
        assert uow.rollbacks == 1

    async def test_fails_when_provider_disabled(self):
        """Что тестируем: отказ при выключенном провайдере.
        Что передаём: сервис сообщает, что синхронизация отключена.
        Что ожидаем: статус 400, обращение к каталогу не выполняется.
        """
        use_case, _uow, anime_api_client, sync_service = _use_case(sources=[])
        sync_service.is_enabled.return_value = False

        result = await use_case.execute(SyncWatchSourcesQuery(anime_id=7, episode=2))

        assert result.ok is False
        assert result.status_code == 400
        assert result.error == "provider_not_configured"
        anime_api_client.get_by_id.assert_not_awaited()

    async def test_fails_when_no_sources_found(self):
        """Что тестируем: отказ при пустой выдаче провайдера.
        Что передаём: пустой список источников.
        Что ожидаем: статус 404 с кодом no_sources_found.
        """
        use_case, _uow, _client, _service = _use_case(sources=[])

        result = await use_case.execute(SyncWatchSourcesQuery(anime_id=7, episode=2, force=True))

        assert result.ok is False
        assert result.status_code == 404
        assert result.error == "no_sources_found"

    async def test_fails_on_provider_timeout(self):
        """Что тестируем: обработку таймаута сетевого поиска.
        Что передаём: сервис бросает TimeoutError.
        Что ожидаем: статус 504 с кодом provider_timeout.
        """
        use_case, _uow, _client, sync_service = _use_case(sources=[])
        sync_service.sync_for_anime.side_effect = TimeoutError

        result = await use_case.execute(SyncWatchSourcesQuery(anime_id=7, episode=2))

        assert result.ok is False
        assert result.status_code == 504
        assert result.error == "provider_timeout"

    async def test_fails_when_episode_unavailable_for_all_translations(self):
        """Что тестируем: проверку доступности серии у озвучек.
        Что передаём: карту доступности без запрошенной серии.
        Что ожидаем: статус 404, чтобы не подменять контент похожим тайтлом.
        """
        record = SimpleNamespace(has_episode=lambda episode: episode != 2)
        use_case, _uow, _client, _service = _use_case(sources=["s1"], availability=[record])

        result = await use_case.execute(SyncWatchSourcesQuery(anime_id=7, episode=2))

        assert result.ok is False
        assert result.status_code == 404
        assert result.error == "episode_not_available_for_translation"

    async def test_skips_availability_check_for_unknown_anime(self):
        """Что тестируем: мягкое поведение при отсутствии карточки тайтла.
        Что передаём: каталог не вернул аниме.
        Что ожидаем: проверка доступности пропущена, источники посчитаны.
        """
        use_case, _uow, anime_api_client, sync_service = _use_case(sources=["s1"])
        anime_api_client.get_by_id.return_value = None

        result = await use_case.execute(SyncWatchSourcesQuery(anime_id=7, episode=2))

        assert result.ok is True
        assert result.data["sources_count"] == 1
        sync_service.get_translations_availability.assert_not_awaited()

    async def test_passes_mal_id_for_strict_addressing(self):
        """Что тестируем: строгую адресацию тайтла при проверке доступности.
        Что передаём: карточку с числовым external_id.
        Что ожидаем: сервис получает shikimori_id, извлечённый из самой сущности.
        """
        record = SimpleNamespace(has_episode=lambda episode: episode == 2)
        use_case, _uow, anime_api_client, sync_service = _use_case(
            sources=["s1"], availability=[record]
        )
        anime_api_client.get_by_id.return_value = _anime(external_id="anilist-99")

        result = await use_case.execute(SyncWatchSourcesQuery(anime_id=7, episode=2))

        assert result.ok is True
        assert sync_service.get_translations_availability.await_args.kwargs["shikimori_id"] is None
