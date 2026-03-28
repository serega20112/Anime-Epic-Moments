from __future__ import annotations

from unittest.mock import Mock

from src.backend.use_case.collection.remove_collection_item import (
    RemoveCollectionItemUseCase,
)


def test_remove_collection_item_use_case_delegates_to_repository():
    """Проверяем, что RemoveCollectionItemUseCase удаляет anime_id из коллекции через репозиторий."""
    repo = Mock()
    use_case = RemoveCollectionItemUseCase(repo)

    use_case.execute(collection_id=3, anime_id=7)

    repo.remove_item.assert_called_once_with(collection_id=3, anime_id=7)
