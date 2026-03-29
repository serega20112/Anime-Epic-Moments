from __future__ import annotations

import pytest

from src.backend.repository.collection_repository import CollectionRepository


def test_collection_repository_is_abstract_and_declares_expected_methods():
    """Проверяем, что контракт CollectionRepository остается абстрактным и полным."""
    assert CollectionRepository.__abstractmethods__ == {
        "create_collection",
        "get_by_id",
        "get_user_collections",
        "get_public_user_collections",
        "add_item",
        "remove_item",
        "get_items",
    }

    with pytest.raises(TypeError):
        CollectionRepository()
