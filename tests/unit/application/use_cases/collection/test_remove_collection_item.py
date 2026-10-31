from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from backend.application.dto import RemoveCollectionItemCommand
from backend.application.use_cases.collection.add_collection_item import CollectionAccessError
from backend.application.use_cases.collection.remove_collection_item import (
    RemoveCollectionItemUseCase,
)
from backend.domain.aggregates.collection.collection import AnimeCollection
from tests.support.fakes import FakeUnitOfWork

COMMAND = RemoveCollectionItemCommand(collection_id=3, anime_id=7, user_id=1)


def _use_case(collection: object) -> tuple[RemoveCollectionItemUseCase, AsyncMock]:
    """Собрать сценарий с репозиторием, возвращающим данную коллекцию.

    Args:
        collection: Значение, которое вернёт ``get_by_id``.

    Returns:
        tuple[RemoveCollectionItemUseCase, AsyncMock]: Сценарий и репозиторий.
    """
    repo = AsyncMock()
    repo.get_by_id = AsyncMock(return_value=collection)
    return RemoveCollectionItemUseCase(FakeUnitOfWork(CollectionRepository=repo)), repo


@pytest.mark.unit
class TestRemoveCollectionItemUseCase:
    """Юнит-тесты удаления аниме из коллекции."""

    async def test_delegates_to_repository(self):
        """Что тестируем: передачу collection_id/anime_id в репозиторий.
        Что передаём: RemoveCollectionItemCommand и коллекцию её владельца.
        Что ожидаем: remove_item вызвана с ожидаемыми аргументами.
        """
        collection = AnimeCollection(user_id=1, title="Своя коллекция", description="")
        use_case, repo = _use_case(collection)

        await use_case.execute(COMMAND)

        repo.remove_item.assert_awaited_once_with(collection_id=3, anime_id=7)

    async def test_rejects_collection_of_another_user(self):
        """Что тестируем: проверку владельца коллекции.
        Что передаём: команду пользователя 1 для коллекции пользователя 99.
        Что ожидаем: CollectionAccessError, удаление не выполняется.
        """
        collection = AnimeCollection(user_id=99, title="Чужая коллекция", description="")
        use_case, repo = _use_case(collection)

        with pytest.raises(CollectionAccessError):
            await use_case.execute(COMMAND)

        repo.remove_item.assert_not_awaited()

    async def test_rejects_missing_collection(self):
        """Что тестируем: удаление из несуществующей коллекции.
        Что передаём: репозиторий, который возвращает None.
        Что ожидаем: CollectionAccessError без попыток удаления.
        """
        use_case, repo = _use_case(None)

        with pytest.raises(CollectionAccessError):
            await use_case.execute(COMMAND)

        repo.remove_item.assert_not_awaited()
