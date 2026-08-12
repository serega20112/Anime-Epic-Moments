from __future__ import annotations

import pytest

from backend.domain.collection.entity import AnimeCollection, AnimeCollectionItem


class TestAnimeCollection:
    """Юнит-тесты агрегата AnimeCollection."""

    @pytest.mark.unit
    def test_validates_and_stores_fields(self):
        """Что тестируем: конструктор AnimeCollection.

        Что передаём: валидную коллекцию с названием, описанием и флагом приватности.
        Что ожидаем: базовые поля коллекции сохраняются корректно.
        """
        collection = AnimeCollection(
            user_id=4,
            title="Лучшие боевики",
            description="Подборка экшена",
            is_public=False,
        )

        assert collection.user_id == 4
        assert collection.title == "Лучшие боевики"
        assert collection.is_public is False

    @pytest.mark.unit
    @pytest.mark.parametrize(
        ("title", "description"),
        [
            ("", ""),
            ("x" * 81, ""),
            ("title", "x" * 401),
        ],
    )
    def test_rejects_invalid_payload(self, title, description):
        """Что тестируем: валидацию AnimeCollection.

        Что передаём: пустое название и превышающие лимит длины название и описание.
        Что ожидаем: выбрасывается ValueError.
        """
        with pytest.raises(ValueError):
            AnimeCollection(user_id=4, title=title, description=description)


class TestAnimeCollectionItem:
    """Юнит-тесты элемента коллекции AnimeCollectionItem."""

    @pytest.mark.unit
    def test_validates_and_normalizes_fields(self):
        """Что тестируем: конструктор AnimeCollectionItem.

        Что передаём: snapshot-метаданные аниме (id, название, жанры).
        Что ожидаем: поля элемента сохраняются корректно.
        """
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