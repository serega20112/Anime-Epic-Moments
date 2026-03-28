from __future__ import annotations

from datetime import datetime
from unittest.mock import Mock

import pytest

from src.backend.domain.collection.entity import AnimeCollection, AnimeCollectionItem
from src.backend.use_case.collection.get_shared_collection import GetSharedCollectionUseCase


def test_get_shared_collection_use_case_rejects_private_collection():
    """Проверяем, что GetSharedCollectionUseCase отклоняет приватную коллекцию."""
    repo = Mock()
    repo.get_by_id.return_value = AnimeCollection(
        id=3,
        user_id=4,
        title="Приватная подборка",
        is_public=False,
    )
    use_case = GetSharedCollectionUseCase(repo)

    with pytest.raises(ValueError):
        use_case.execute(3)


def test_get_shared_collection_use_case_maps_public_collection():
    """Проверяем, что GetSharedCollectionUseCase собирает share-представление публичной коллекции."""
    repo = Mock()
    repo.get_by_id.return_value = AnimeCollection(
        id=3,
        user_id=4,
        title="Публичная подборка",
        description="desc",
        is_public=True,
        created_at=datetime(2026, 3, 28),
    )
    repo.get_items.return_value = [
        AnimeCollectionItem(
            collection_id=3,
            anime_id=7,
            title="Gintama",
        )
    ]
    use_case = GetSharedCollectionUseCase(repo)

    result = use_case.execute(3)

    assert result.collection.title == "Публичная подборка"
    assert result.items[0].anime_id == 7
