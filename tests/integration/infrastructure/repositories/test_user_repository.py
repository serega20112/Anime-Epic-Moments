from __future__ import annotations

import pytest

from backend.domain import User
from backend.infrastructure.repositories.user_repository import UserRepository


@pytest.mark.integration
class TestUserRepository:
    """Интеграционные тесты UserRepository на in-memory базе."""

    @pytest.mark.parametrize(
        ("lookup_method", "value_getter"),
        [
            ("get_by_id", lambda user: user.id),
            ("get_by_email", lambda user: user.email),
        ],
    )
    async def test_adds_and_loads_user(self, async_db_session, lookup_method, value_getter):
        """Проверяем, что UserRepository сохраняет пользователя и читает его по id и email."""
        repo = UserRepository(async_db_session)
        created = await repo.add(
            User(
                email="repo@example.com",
                username="repo-user",
                password_hash="hash-1",
            )
        )

        loaded = await getattr(repo, lookup_method)(value_getter(created))

        assert created.id is not None
        assert created.created_at is not None
        assert loaded is not None
        assert loaded.email == "repo@example.com"
        assert loaded.username == "repo-user"

    async def test_updates_profile_fields(self, async_db_session):
        """Проверяем, что UserRepository обновляет username и avatar_url существующего пользователя."""
        repo = UserRepository(async_db_session)
        user = await repo.add(
            User(
                email="profile@example.com",
                username="before",
                password_hash="hash-1",
            )
        )
        await user.change_username("after")
        await user.update_avatar("https://example.com/avatar.png")

        updated = await repo.update(user)
        loaded = await repo.get_by_id(user.id)

        assert updated.username == "after"
        assert loaded is not None
        assert loaded.username == "after"
        assert loaded.avatar_url == "https://example.com/avatar.png"

    async def test_updates_password_hash(self, async_db_session):
        """Проверяем, что UserRepository обновляет password_hash и возвращает актуального пользователя."""
        repo = UserRepository(async_db_session)
        user = await repo.add(
            User(
                email="password@example.com",
                username="tester",
                password_hash="old-hash",
            )
        )

        updated = await repo.update_password(user.id, "new-hash")
        loaded = await repo.get_by_id(user.id)

        assert updated.password_hash == "new-hash"
        assert loaded.password_hash == "new-hash"

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
    async def test_raises_for_missing_user_on_update(self, async_db_session, action):
        """Проверяем, что UserRepository не обновляет несуществующего пользователя."""
        repo = UserRepository(async_db_session)

        with pytest.raises(ValueError):
            await action(repo)

    @pytest.mark.parametrize("follow_action", ["follow", "unfollow"])
    async def test_manages_follow_relationships(self, async_db_session, follow_action):
        """Проверяем, что UserRepository создает и удаляет подписки, а также считает follower/following stats."""
        repo = UserRepository(async_db_session)
        follower = await repo.add(
            User(
                email="follower@example.com",
                username="follower",
                password_hash="hash-1",
            )
        )
        followed = await repo.add(
            User(
                email="followed@example.com",
                username="followed",
                password_hash="hash-2",
            )
        )

        await repo.follow(follower.id, followed.id)
        if follow_action == "unfollow":
            await repo.unfollow(follower.id, followed.id)

        followers_count, following_count = await repo.get_follow_stats(followed.id)
        followed_user_ids = await repo.get_followed_user_ids(follower.id)

        assert await repo.is_following(follower.id, followed.id) is (follow_action == "follow")
        assert followed_user_ids == ([followed.id] if follow_action == "follow" else [])
        assert followers_count == (1 if follow_action == "follow" else 0)
        assert following_count == 0

    async def test_rejects_self_follow(self, async_db_session):
        """Проверяем, что UserRepository не позволяет подписаться на самого себя."""
        repo = UserRepository(async_db_session)
        user = await repo.add(
            User(
                email="self@example.com",
                username="self-user",
                password_hash="hash-1",
            )
        )

        with pytest.raises(ValueError):
            await repo.follow(user.id, user.id)
