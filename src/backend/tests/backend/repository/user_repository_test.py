from __future__ import annotations

import pytest

from src.backend.repository.user_repository import UserRepository


def test_user_repository_is_abstract_and_declares_expected_methods():
    """Проверяем, что контракт UserRepository остается абстрактным и полным."""
    assert UserRepository.__abstractmethods__ == {
        "add",
        "get_by_email",
        "get_by_id",
        "get_by_ids",
        "follow",
        "unfollow",
        "is_following",
        "get_follow_stats",
        "get_followed_user_ids",
        "get_followed_users",
        "get_followers",
        "update",
        "update_password",
    }

    with pytest.raises(TypeError):
        UserRepository()
