from __future__ import annotations

from datetime import datetime
from unittest.mock import Mock

from backend.application.use_cases import GetUserCollectionsUseCase
from backend.domain.collection.entity import AnimeCollection, AnimeCollectionItem


def test_get_user_collections_use_case_maps_entities_to_view_models():
    """Проверяем, что GetUserCollectionsUseCase собирает карточки коллекций и элементы с watch_url."""
    repo = Mock()
    repo.get_user_collections.return_value = [
        AnimeCollection(
            id=1,
            user_id=4,
            title="Лучшие боевики",
            description="Подборка экшена",
            created_at=datetime(2026, 3, 28),
        )
    ]
    repo.get_items_count_map.return_value = {1: 1}
    repo.get_items.return_value = [
        AnimeCollectionItem(
            collection_id=1,
            anime_id=7,
            title="Gintama",
            genres=["Comedy"],
        )
    ]
    use_case = GetUserCollectionsUseCase(repo)

    result = use_case.execute(4)

    assert result[0].collection.title == "Лучшие боевики"
    assert result[0].items[0].watch_url == "/watch/7?episode=1"
