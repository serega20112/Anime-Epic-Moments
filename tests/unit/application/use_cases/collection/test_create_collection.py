from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from backend.application.dto import CreateCollectionCommand
from backend.application.use_cases.collection.create_collection import CreateCollectionUseCase


@pytest.mark.unit
class TestCreateCollectionUseCase:
    """Юнит-тесты создания коллекции аниме."""

    async def test_builds_and_saves_collection(self):
        """Что тестируем: сборку и сохранение коллекции.
        Что передаём: CreateCollectionCommand с данными формы.
        Что ожидаем: create_collection вызвана, возвращаются поля коллекции.
        """
        repo = AsyncMock()
        repo.create_collection.side_effect = lambda collection: collection
        use_case = CreateCollectionUseCase(repo)

        result = await use_case.execute(
            CreateCollectionCommand(
                user_id=4,
                title="Лучшие боевики",
                description="Подборка экшена",
                is_public=False,
            )
        )

        assert result.user_id == 4
        assert result.title == "Лучшие боевики"
        assert result.is_public is False