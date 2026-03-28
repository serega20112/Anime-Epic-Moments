from __future__ import annotations

from unittest.mock import Mock

from src.backend.use_case.collection.add_collection_item import AddCollectionItemUseCase


def test_add_collection_item_use_case_builds_snapshot_and_saves_it():
    """Проверяем, что AddCollectionItemUseCase собирает snapshot аниме и сохраняет его в коллекцию."""
    repo = Mock()
    repo.add_item.side_effect = lambda item: item
    use_case = AddCollectionItemUseCase(repo)

    result = use_case.execute(
        collection_id=3,
        anime_id=7,
        title="Gintama",
        description="Comedy",
        cover_url="https://example.com/cover.jpg",
        genres=["Comedy", "Action"],
    )

    assert result.collection_id == 3
    assert result.anime_id == 7
    assert result.genres == ["Comedy", "Action"]
