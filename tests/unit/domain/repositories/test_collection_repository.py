from __future__ import annotations

from backend.application.interface.repositories.collection_repository import CollectionRepository


class TestCollectionRepository:
    def test_abstract_method_names(self):
        assert {
            "create_collection",
            "get_by_id",
            "get_user_collections",
            "get_public_user_collections",
            "add_item",
            "remove_item",
            "get_items",
        } <= set(CollectionRepository.__abstractmethods__)

    def test_cannot_be_instantiated(self):
        try:
            CollectionRepository()  # type: ignore[abstract]
            raised = False
        except TypeError:
            raised = True
        assert raised is True
