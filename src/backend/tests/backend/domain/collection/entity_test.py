from __future__ import annotations

import pytest

from src.backend.domain.collection.entity import AnimeCollection, AnimeCollectionItem


def test_anime_collection_validates_and_stores_fields():
    """Проверяем, что AnimeCollection сохраняет базовые поля валидной коллекции."""
    collection = AnimeCollection(
        user_id=4,
        title="Лучшие боевики",
        description="Подборка экшена",
        is_public=False,
    )

    assert collection.user_id == 4
    assert collection.title == "Лучшие боевики"
    assert collection.is_public is False


@pytest.mark.parametrize(
    ("title", "description"),
    [
        ("", ""),
        ("x" * 81, ""),
        ("title", "x" * 401),
    ],
)
def test_anime_collection_rejects_invalid_payload(title, description):
    """Проверяем, что AnimeCollection отклоняет пустое название и слишком длинные поля."""
    with pytest.raises(ValueError):
        AnimeCollection(user_id=4, title=title, description=description)


def test_anime_collection_item_validates_and_normalizes_fields():
    """Проверяем, что AnimeCollectionItem сохраняет snapshot-метаданные аниме."""
    item = AnimeCollectionItem(
        collection_id=2,
        anime_id=7,
        title="Gintama",
        description="Комедийный экшен",
        cover_url="https://example.com/cover.jpg",
        genres=["Comedy", "Action"],
    )

    assert item.collection_id == 2
    assert item.anime_id == 7
    assert item.genres == ["Comedy", "Action"]
