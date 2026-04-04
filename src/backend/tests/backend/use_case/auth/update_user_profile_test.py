from __future__ import annotations

import pytest
from unittest.mock import Mock

from src.backend.domain.user.entity import User
from src.backend.use_case.auth.update_user_profile import (
    InvalidProfileDataError,
    UpdateUserProfileUseCase,
    UserNotFoundError,
)


def test_update_user_profile_rejects_missing_user():
    """Проверяем, что UpdateUserProfileUseCase не обновляет отсутствующего пользователя."""
    user_repo = Mock()
    user_repo.get_by_id.return_value = None
    use_case = UpdateUserProfileUseCase(user_repo)

    with pytest.raises(UserNotFoundError):
        use_case.execute(1, "tester", None)


@pytest.mark.parametrize("username", ["", "  ", "ab", "x" * 21])
def test_update_user_profile_rejects_invalid_username(username):
    """Проверяем, что UpdateUserProfileUseCase валидирует пустой и некорректный username."""
    user_repo = Mock()
    user_repo.get_by_id.return_value = User(
        id=1,
        email="user@example.com",
        username="tester",
        password_hash="hash",
    )
    use_case = UpdateUserProfileUseCase(user_repo)

    with pytest.raises(InvalidProfileDataError):
        use_case.execute(1, username, "https://example.com/avatar.png")


def test_update_user_profile_trims_and_persists_fields():
    """Проверяем, что UpdateUserProfileUseCase нормализует данные и сохраняет обновленного пользователя."""
    user = User(
        id=1,
        email="user@example.com",
        username="tester",
        password_hash="hash",
    )
    user_repo = Mock()
    user_repo.get_by_id.return_value = user
    user_repo.update.return_value = user
    profile_cache = Mock()
    use_case = UpdateUserProfileUseCase(user_repo, profile_cache)

    result = use_case.execute(1, "  updated-name  ", "  https://example.com/avatar.png  ")

    assert result.username == "updated-name"
    assert result.avatar_url == "https://example.com/avatar.png"
    user_repo.update.assert_called_once_with(user)
    profile_cache.invalidate_overview.assert_called_once_with(1)
