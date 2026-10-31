"""DTO коллекций аниме."""

from backend.application.dto.collection.add_collection_item_command import AddCollectionItemCommand
from backend.application.dto.collection.create_collection_command import CreateCollectionCommand
from backend.application.dto.collection.get_shared_collection_query import GetSharedCollectionQuery
from backend.application.dto.collection.get_user_collections_query import GetUserCollectionsQuery
from backend.application.dto.collection.remove_collection_item_command import (
    RemoveCollectionItemCommand,
)

__all__ = [
    "AddCollectionItemCommand",
    "CreateCollectionCommand",
    "GetSharedCollectionQuery",
    "GetUserCollectionsQuery",
    "RemoveCollectionItemCommand",
]
