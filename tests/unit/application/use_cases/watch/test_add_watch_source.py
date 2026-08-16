from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from backend.application.use_cases import AddWatchSourceUseCase
from backend.domain import Translation, WatchSource


@pytest.mark.unit
class TestAddWatchSourceUseCase:
    """Юнит-тесты добавления озвучки и источника просмотра."""

    async def test_creates_translation_then_source(self):
        """Что тестируем: сначала создается перевод, затем источник просмотра.
        Что передаём: параметры озвучки и источника.
        Что ожидаем: перевод и источник созданы, источник ссылается на перевод.
        """
        watch_repo = AsyncMock()
        watch_repo.add_translation.return_value = Translation(
            id=9,
            anime_id=7,
            name="AniLibria",
            translation_type="voice",
        )
        watch_repo.add_source.return_value = WatchSource(
            id=15,
            anime_id=7,
            episode=2,
            translation_id=9,
            provider_name="Kodik",
            source_name="s1",
            stream_url="https://example.com/stream.m3u8",
            quality_label="1080",
        )
        use_case = AddWatchSourceUseCase(watch_repo, AsyncMock())

        result = await use_case.execute(
            anime_id=7,
            episode=2,
            translation_name="AniLibria",
            translation_type="voice",
            provider_name="Kodik",
            source_name="s1",
            stream_url="https://example.com/stream.m3u8",
            quality_label="1080",
        )

        assert result.id == 15
        translation = watch_repo.add_translation.await_args.args[0]
        source = watch_repo.add_source.await_args.args[0]
        assert translation.name == "AniLibria"
        assert source.translation_id == 9
        assert source.provider_name == "Kodik"
