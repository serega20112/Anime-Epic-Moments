from __future__ import annotations

import pytest

from src.backend.domain.favorite.entity import Favorite
from src.backend.domain.user.entity import User
from src.backend.infrastructure.repositories.favorite_repository import FavoriteRepository
from src.backend.infrastructure.repositories.user_repository import UserRepository


def test_favorite_repository_adds_and_reads_snapshot_payload(db_session):
    """Проверяем, что FavoriteRepository сохраняет snapshot-поля и жанры карточки избранного."""
    user = UserRepository(db_session).add(
        User(email="fav@example.com", username="favorite-user", password_hash="hash")
    )
    repo = FavoriteRepository(db_session)
    repo.add(
        Favorite(
            user_id=user.id,
            anime_id=185,
            title="Initial D First Stage",
            description="Street racing",
            cover_url="https://example.com/initial-d.jpg",
            genres=["Action", "", "Cars"],
        )
    )

    items = repo.get_by_user(user.id)

    assert len(items) == 1
    assert items[0].title == "Initial D First Stage"
    assert items[0].genres == ["Action", "Cars"]


@pytest.mark.parametrize("exists", [False, True])
def test_favorite_repository_remove_deletes_existing_entry_and_ignores_missing(
    db_session,
    exists,
):
    """Проверяем, что FavoriteRepository удаляет существующую запись и спокойно игнорирует отсутствующую."""
    user = UserRepository(db_session).add(
        User(email="remove@example.com", username="remove-user", password_hash="hash")
    )
    repo = FavoriteRepository(db_session)
    if exists:
        repo.add(Favorite(user_id=user.id, anime_id=7))

    repo.remove(user.id, 7)

    assert repo.get_by_user(user.id) == []


@pytest.mark.parametrize(
    ("genres", "expected_dump", "payload", "expected_load"),
    [
        (["Action", "", "Cars"], '["Action", "Cars"]', '["Action", "", "Cars"]', ["Action", "Cars"]),
        ([], None, None, []),
        (None, None, '{"foo":"bar"}', []),
    ],
)
def test_favorite_repository_serializes_and_deserializes_genres(
    db_session,
    genres,
    expected_dump,
    payload,
    expected_load,
):
    """Проверяем, что FavoriteRepository чистит жанры при сериализации и безопасно читает JSON."""
    repo = FavoriteRepository(db_session)

    assert repo._dump_genres(genres) == expected_dump
    assert repo._load_genres(payload) == expected_load
