from __future__ import annotations

from unittest.mock import Mock

from src.backend.use_case.collection.create_collection import CreateCollectionUseCase


def test_create_collection_use_case_builds_and_saves_collection():
    """Проверяем, что CreateCollectionUseCase собирает коллекцию и отдает ее в репозиторий."""
    repo = Mock()
    repo.create_collection.side_effect = lambda collection: collection
    use_case = CreateCollectionUseCase(repo)

    result = use_case.execute(
        user_id=4,
        title="Лучшие боевики",
        description="Подборка экшена",
        is_public=False,
    )

    assert result.user_id == 4
    assert result.title == "Лучшие боевики"
    assert result.is_public is False
