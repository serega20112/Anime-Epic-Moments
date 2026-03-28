from src.backend.domain.collection.entity import AnimeCollection
from src.backend.repository.collection_repository import CollectionRepository


class CreateCollectionUseCase:
    """Создает пользовательскую коллекцию аниме."""

    def __init__(self, collection_repo: CollectionRepository):
        self.collection_repo = collection_repo

    def execute(
        self,
        user_id: int,
        title: str,
        description: str = "",
        is_public: bool = True,
    ) -> AnimeCollection:
        collection = AnimeCollection(
            user_id=user_id,
            title=title,
            description=description,
            is_public=is_public,
        )
        return self.collection_repo.create_collection(collection)
