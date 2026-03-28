from __future__ import annotations

import pytest

from src.backend.domain.user.entity import User
from src.backend.infrastructure.repositories.user_repository import UserRepository


@pytest.mark.parametrize(
    ("lookup_method", "value_getter"),
    [
        ("get_by_id", lambda user: user.id),
        ("get_by_email", lambda user: user.email),
    ],
)
def test_user_repository_adds_and_loads_user(db_session, lookup_method, value_getter):
    """Проверяем, что UserRepository сохраняет пользователя и читает его по id и email."""
    repo = UserRepository(db_session)
    created = repo.add(
        User(
            email="repo@example.com",
            username="repo-user",
            password_hash="hash-1",
        )
    )

    loaded = getattr(repo, lookup_method)(value_getter(created))

    assert created.id is not None
    assert created.created_at is not None
    assert loaded is not None
    assert loaded.email == "repo@example.com"
    assert loaded.username == "repo-user"


def test_user_repository_updates_profile_fields(db_session):
    """Проверяем, что UserRepository обновляет username и avatar_url существующего пользователя."""
    repo = UserRepository(db_session)
    user = repo.add(
        User(
            email="profile@example.com",
            username="before",
            password_hash="hash-1",
        )
    )
    user.change_username("after")
    user.update_avatar("https://example.com/avatar.png")

    updated = repo.update(user)
    loaded = repo.get_by_id(user.id)

    assert updated.username == "after"
    assert loaded is not None
    assert loaded.username == "after"
    assert loaded.avatar_url == "https://example.com/avatar.png"


def test_user_repository_updates_password_hash(db_session):
    """Проверяем, что UserRepository обновляет password_hash и возвращает актуального пользователя."""
    repo = UserRepository(db_session)
    user = repo.add(
        User(
            email="password@example.com",
            username="tester",
            password_hash="old-hash",
        )
    )

    updated = repo.update_password(user.id, "new-hash")

    assert updated.password_hash == "new-hash"
    assert repo.get_by_id(user.id).password_hash == "new-hash"


@pytest.mark.parametrize(
    "action",
    [
        lambda repo: repo.update(
            User(
                id=999,
                email="missing@example.com",
                username="ghost",
                password_hash="hash",
            )
        ),
        lambda repo: repo.update_password(999, "hash"),
    ],
)
def test_user_repository_raises_for_missing_user_on_update(db_session, action):
    """Проверяем, что UserRepository не обновляет несуществующего пользователя."""
    repo = UserRepository(db_session)

    with pytest.raises(ValueError):
        action(repo)
