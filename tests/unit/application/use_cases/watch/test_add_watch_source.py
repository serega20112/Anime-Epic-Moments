from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from backend.application.dto import AddWatchSourceCommand
from backend.application.use_cases import AddWatchSourceUseCase
from backend.domain import Translation, WatchSource
from tests.support.fakes import FakeUnitOfWork


def _command(**overrides) -> AddWatchSourceCommand:
    """Собрать команду добавления источника с переопределёнными полями."""
    fields = {
        "anime_id": 7,
        "episode": 2,
        "translation_name": "AniLibria",
        "translation_type": "dub",
        "provider_name": "Kinobox",
        "source_name": "kinobox-1080",
        "stream_url": "https://example.com/stream.m3u8",
        "quality_label": "1080p",
    }
    fields.update(overrides)
    return AddWatchSourceCommand(**fields)


@pytest.mark.unit
class TestAddWatchSourceUseCase:
    """Юнит-тесты ручного добавления источника просмотра."""

    async def test_creates_translation_then_source(self):
        """Что тестируем: последовательное создание озвучки и источника.
        Что передаём: команду нового источника с языком по умолчанию.
        Что ожидаем: озвучка сохранена, источник ссылается на её идентификатор.
        """
        repository = AsyncMock()
        repository.add_source.side_effect = lambda item: item
        repository.add_translation.return_value = Translation(
            id=3, anime_id=7, name="AniLibria", translation_type="dub"
        )
        uow = FakeUnitOfWork(WatchRepository=repository)
        use_case = AddWatchSourceUseCase(uow)

        source = await use_case.execute(_command())

        assert uow.commits == 1
        assert isinstance(source, WatchSource)
        assert source.translation_id == 3
        assert source.provider_name == "Kinobox"
        saved_translation = repository.add_translation.await_args.args[0]
        assert saved_translation.language == "ru"

    async def test_uses_zero_when_translation_unsaved(self):
        """Что тестируем: поведение при отсутствии идентификатора у озвучки.
        Что передаём: озвучку без идентификатора.
        Что ожидаем: источник создан с translation_id=0.
        """
        repository = AsyncMock()
        repository.add_translation.return_value = Translation(
            anime_id=7, name="AniLibria", translation_type="dub", id=None
        )
        repository.add_source.side_effect = lambda item: item
        use_case = AddWatchSourceUseCase(FakeUnitOfWork(WatchRepository=repository))

        source = await use_case.execute(_command(language="en", source_type="cdn"))

        assert source.translation_id == 0
        assert source.source_type == "cdn"
