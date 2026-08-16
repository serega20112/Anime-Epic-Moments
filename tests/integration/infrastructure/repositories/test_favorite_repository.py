from __future__ import annotations

import pytest

from backend.domain import Favorite, User
from backend.infrastructure.repositories.favorite_repository import FavoriteRepository
from backend.infrastructure.repositories.user_repository import UserRepository


@pytest.mark.integration
class TestFavoriteRepository:
    """Интеграционные тесты FavoriteRepository на in-memory базе."""

    async def test_adds_and_reads_snapshot_payload(self, async_db_session):
        """Проверяем, что FavoriteRepository сохраняет snapshot-поля и жанры карточки избранного."""
        user = await UserRepository(async_db_session).add(
            User(email="fav@example.com", username="favorite-user", password_hash="hash")
        )
        repo = FavoriteRepository(async_db_session)
        await repo.add(
            Favorite(
                user_id=user.id,
                anime_id=185,
                title="Initial D First Stage",
                description="Street racing",
                cover_url="https://example.com/initial-d.jpg",
                genres=["Action", "", "Cars"],
            )
        )

        items = await repo.get_by_user(user.id)

        assert len(items) == 1
        assert items[0].title == "Initial D First Stage"
        assert items[0].genres == ["Action", "Cars"]

    @pytest.mark.parametrize("exists", [False, True])
    async def test_remove_deletes_existing_entry_and_ignores_missing(
        self, async_db_session, exists
    ):
        """Проверяем, что FavoriteRepository удаляет существующую запись и спокойно игнорирует отсутствующую."""
        user = await UserRepository(async_db_session).add(
            User(email="remove@example.com", username="remove-user", password_hash="hash")
        )
        repo = FavoriteRepository(async_db_session)
        if exists:
            await repo.add(Favorite(user_id=user.id, anime_id=7))

        await repo.remove(user.id, 7)

        assert await repo.get_by_user(user.id) == []

    @pytest.mark.parametrize(
        ("genres", "expected_dump", "payload", "expected_load"),
        [
            (
                ["Action", "", "Cars"],
                '["Action", "Cars"]',
                '["Action", "", "Cars"]',
                ["Action", "Cars"],
            ),
            ([], None, None, []),
            (None, None, '{"foo":"bar"}', []),
        ],
    )
    def test_serializes_and_deserializes_genres(
        self, genres, expected_dump, payload, expected_load
    ):
        """Проверяем, что FavoriteRepository чистит жанры при сериализации и безопасно читает JSON."""
        repo = FavoriteRepository(None)

        assert repo._dump_genres(genres) == expected_dump
        assert repo._load_genres(payload) == expected_load
