from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from backend.application.dto import SaveViewingSessionCommand
from backend.application.use_cases.watch.session.save_viewing_session import (
    SaveViewingSessionUseCase,
)
from backend.domain import ViewingSession
from tests.support.fakes import FakeUnitOfWork


def _use_case(repository: AsyncMock) -> tuple:
    """Собрать сценарий сохранения сессии с двойниками репозитория и кэша."""
    profile_cache = AsyncMock()
    uow = FakeUnitOfWork(WatchRepository=repository)
    return SaveViewingSessionUseCase(uow, profile_cache), uow, repository, profile_cache


def _command(**overrides) -> SaveViewingSessionCommand:
    """Собрать команду сохранения сессии с переопределёнными полями."""
    fields = {
        "user_id": 4,
        "anime_id": 7,
        "episode": 2,
        "watch_source_id": 11,
        "position_seconds": 120.0,
        "volume": 0.8,
        "quality_label": "1080p",
        "is_paused": False,
    }
    fields.update(overrides)
    return SaveViewingSessionCommand(**fields)


@pytest.mark.unit
class TestSaveViewingSessionUseCase:
    """Юнит-тесты сохранения позиции просмотра."""

    async def test_upserts_domain_session_and_invalidates_cache(self):
        """Что тестируем: сохранение доменной сессии и инвалидацию кэша профиля.
        Что передаём: полную команду состояния плеера.
        Что ожидаем: сессия сохранена, кэш очищен, транзакция зафиксирована.
        """
        repository = AsyncMock()
        repository.upsert_session.side_effect = lambda item: item
        use_case, uow, _repository, profile_cache = _use_case(repository)

        result = await use_case.execute(_command())

        assert result.ok is True
        assert isinstance(result.data, ViewingSession)
        assert result.data.position_seconds == 120.0
        assert uow.commits == 1
        saved = repository.upsert_session.await_args.args[0]
        assert isinstance(saved, ViewingSession)
        assert saved.quality_label == "1080p"
        profile_cache.invalidate_overview.assert_awaited_once_with(4)

    async def test_normalizes_optional_values(self):
        """Что тестируем: подстановку значений по умолчанию для пустых полей.
        Что передаём: пустую метку качества.
        Что ожидаем: сохранена метка 'Auto'.
        """
        repository = AsyncMock()
        repository.upsert_session.side_effect = lambda item: item
        use_case, _uow, _repository, _profile_cache = _use_case(repository)

        result = await use_case.execute(_command(quality_label=""))

        assert result.data.quality_label == "Auto"

    @pytest.mark.parametrize(
        "overrides",
        [{"episode": None}, {"watch_source_id": None}],
    )
    async def test_rejects_incomplete_payload(self, overrides):
        """Что тестируем: отказ при отсутствии обязательных полей плеера.
        Что передаём: команду без episode либо без watch_source_id.
        Что ожидаем: статус 400, сессия не сохраняется, кэш не трогается.
        """
        repository = AsyncMock()
        use_case, _uow, _repository, profile_cache = _use_case(repository)

        result = await use_case.execute(_command(**overrides))

        assert result.ok is False
        assert result.status_code == 400
        assert result.error == "invalid_payload"
        repository.upsert_session.assert_not_awaited()
        profile_cache.invalidate_overview.assert_not_awaited()
