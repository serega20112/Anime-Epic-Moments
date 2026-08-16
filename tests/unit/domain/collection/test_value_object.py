from __future__ import annotations

from dataclasses import asdict

import pytest

from backend.domain.collection.value_object import (
    CollectionCard,
    CollectionDetails,
    CollectionItemCard,
)


class TestCollectionValueObjects:
    """Юнит-тесты value objects коллекций."""

    @pytest.mark.unit
    def test_stores_render_payload(self):
        """Что тестируем: структуру value objects коллекций.

        Что передаём: карточку элемента, карточку коллекции и детальное представление.
        Что ожидаем: детальное представление собирает корректный payload для рендера.
        """
        item = CollectionItemCard(
            anime_id=7,
            title="Gintama",
            description="Comedy",
            cover_url="https://example.com/cover.jpg",
            genres=["Comedy"],
            watch_url="/watch/7?episode=1",
        )
        details = CollectionDetails(
            collection=CollectionCard(
                id=1,
                title="Лучшие комедии",
                description="Подборка на вечер",
                items_count=1,
                is_public=True,
                created_at="2026-03-28",
                share_url="/collections/share/1",
            ),
            items=[item],
        )

        payload = asdict(details)

        assert payload["collection"]["title"] == "Лучшие комедии"
        assert payload["items"][0]["anime_id"] == 7
