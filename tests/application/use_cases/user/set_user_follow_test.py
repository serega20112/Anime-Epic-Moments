from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from backend.application.use_cases import SetUserFollowUseCase


@pytest.mark.parametrize(
    ("follow", "expected_method"),
    [
        (True, "follow"),
        (False, "unfollow"),
    ],
)
def test_set_user_follow_use_case_delegates_to_expected_repository_method(
        follow,
        expected_method,
):
    """Проверяем, что SetUserFollowUseCase вызывает follow или unfollow в зависимости от команды."""
    user_repo = Mock()
    profile_cache = Mock()
    user_repo.get_by_id.return_value = SimpleNamespace(id=7)
    getattr(user_repo, expected_method).return_value = follow
    use_case = SetUserFollowUseCase(user_repo, profile_cache)

    result = use_case.execute(
        follower_user_id=3,
        followed_user_id=7,
        follow=follow,
    )

    assert result is follow
    getattr(user_repo, expected_method).assert_called_once_with(3, 7)
    profile_cache.invalidate_overview.assert_any_call(3)
    profile_cache.invalidate_overview.assert_any_call(7)


def test_set_user_follow_use_case_rejects_missing_target_user():
    """Проверяем, что SetUserFollowUseCase не создает подписку на несуществующего пользователя."""
    user_repo = Mock()
    user_repo.get_by_id.return_value = None
    use_case = SetUserFollowUseCase(user_repo)

    with pytest.raises(ValueError):
        use_case.execute(follower_user_id=3, followed_user_id=99, follow=True)
