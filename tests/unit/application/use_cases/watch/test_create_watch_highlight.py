from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from backend.application.dto import CreateWatchHighlightCommand
from backend.application.use_cases.result import UseCaseResult
from backend.application.use_cases.watch.highlight.create_watch_highlight import (
    CreateWatchHighlightUseCase,
)
from backend.domain import HighlightContext
from tests.support.fakes import FakeUnitOfWork


def _command(**overrides) -> CreateWatchHighlightCommand:
    """Собрать команду хайлайта из плеера с переопределёнными полями."""
    fields = {
        "user_id": 4,
        "anime_id": 7,
        "episode": 2,
        "title": "Финал заезда",
        "category": "гонки",
        "start_timestamp": 10.0,
        "end_timestamp": 25.0,
        "description": "обгон на последнем повороте",
        "is_spoiler": False,
        "emotion": "hype",
        "watch_source_id": 11,
        "translation_id": 3,
        "original_title": "Gintama",
    }
    fields.update(overrides)
    return CreateWatchHighlightCommand(**fields)


def _use_case(create_result: UseCaseResult, repository: AsyncMock) -> tuple:
    """Собрать сценарий с заданным результатом создания хайлайта."""
    create_highlight = AsyncMock()
    create_highlight.execute.return_value = create_result
    uow = FakeUnitOfWork(WatchRepository=repository)
    return CreateWatchHighlightUseCase(uow, create_highlight), uow, create_highlight


@pytest.mark.unit
class TestCreateWatchHighlightUseCase:
    """Юнит-тесты создания хайлайта из плеера."""

    async def test_creates_highlight_and_context(self):
        """Что тестируем: создание хайлайта и сохранение контекста плеера.
        Что передаём: полную команду и успешный результат вложенного сценария.
        Что ожидаем: контекст привязан к идентификатору хайлайта, статус 201.
        """
        repository = AsyncMock()
        created = UseCaseResult(ok=True, status_code=201, data=SimpleNamespace(id=55))
        use_case, uow, create_highlight = _use_case(created, repository)

        result = await use_case.execute(_command())

        assert result.ok is True
        assert result.status_code == 201
        assert result.data.id == 55
        assert uow.commits == 1
        create_highlight.execute.assert_awaited_once()
        context = repository.add_highlight_context.await_args.args[0]
        assert isinstance(context, HighlightContext)
        assert context.highlight_id == 55
        assert context.watch_source_id == 11
        assert context.original_title == "Gintama"

    async def test_propagates_highlight_failure(self):
        """Что тестируем: проброс отказа вложенного сценария создания хайлайта.
        Что передаём: результат failure со статусом 403.
        Что ожидаем: тот же статус и код, контекст не сохраняется.
        """
        repository = AsyncMock()
        failure = UseCaseResult(ok=False, status_code=403, error="quota_exceeded")
        use_case, _uow, _create_highlight = _use_case(failure, repository)

        result = await use_case.execute(_command())

        assert result.ok is False
        assert result.status_code == 403
        assert result.error == "quota_exceeded"
        repository.add_highlight_context.assert_not_awaited()

    @pytest.mark.parametrize(
        "overrides",
        [
            {"episode": None},
            {"watch_source_id": None},
            {"translation_id": None},
            {"start_timestamp": None},
            {"end_timestamp": None},
        ],
    )
    async def test_rejects_incomplete_payload(self, overrides):
        """Что тестируем: отказ при неполном наборе полей плеера.
        Что передаём: команду с отсутствующим обязательным полем.
        Что ожидаем: статус 400, вложенный сценарий не вызывается.
        """
        repository = AsyncMock()
        created = UseCaseResult(ok=True, status_code=201, data=SimpleNamespace(id=55))
        use_case, _uow, create_highlight = _use_case(created, repository)

        result = await use_case.execute(_command(**overrides))

        assert result.ok is False
        assert result.status_code == 400
        assert result.error == "invalid_payload"
        create_highlight.execute.assert_not_awaited()
