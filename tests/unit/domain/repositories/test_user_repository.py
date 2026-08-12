from __future__ import annotations

from backend.domain.repositories.user_repository import UserRepository


class TestUserRepository:
    def test_abstract_method_names(self):
        assert {
            "add",
            "get_by_email",
            "get_by_id",
            "update",
            "update_password",
            "get_by_ids",
            "follow",
            "unfollow",
            "is_following",
            "get_follow_stats",
            "get_followed_user_ids",
            "get_followed_users",
            "get_followers",
        } <= set(UserRepository.__abstractmethods__)

    def test_cannot_be_instantiated(self):
        try:
            UserRepository()  # type: ignore[abstract]
            raised = False
        except TypeError:
            raised = True
        assert raised is True