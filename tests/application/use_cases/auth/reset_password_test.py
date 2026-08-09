from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import Mock

import jwt
import pytest

from backend.application.use_cases.auth.reset_password import (
    InvalidPasswordResetTokenError,
    ResetPasswordUseCase,
)


def test_reset_password_rejects_invalid_token():
    """Проверяем, что ResetPasswordUseCase отклоняет неверный или просроченный токен."""
    user_repo = Mock()
    jwt_service = Mock()
    jwt_service.decode_password_reset_token.side_effect = jwt.InvalidTokenError("bad token")
    use_case = ResetPasswordUseCase(user_repo, jwt_service, Mock())

    with pytest.raises(InvalidPasswordResetTokenError):
        use_case.execute("bad-token", "new-password")


def test_reset_password_rejects_missing_user():
    """Проверяем, что ResetPasswordUseCase отклоняет токен пользователя, которого нет в репозитории."""
    user_repo = Mock()
    user_repo.get_by_id.return_value = None
    jwt_service = Mock()
    jwt_service.decode_password_reset_token.return_value = 17
    use_case = ResetPasswordUseCase(user_repo, jwt_service, Mock())

    with pytest.raises(InvalidPasswordResetTokenError):
        use_case.execute("token", "new-password")


def test_reset_password_hashes_and_persists_new_password():
    """Проверяем, что ResetPasswordUseCase хеширует пароль и сохраняет его через репозиторий."""
    user_repo = Mock()
    user_repo.get_by_id.return_value = SimpleNamespace(id=17)
    user_repo.update_password.return_value = SimpleNamespace(id=17, password_hash="new-hash")
    jwt_service = Mock()
    jwt_service.decode_password_reset_token.return_value = 17
    password_service = Mock()
    password_service.hash_password.return_value = "new-hash"
    use_case = ResetPasswordUseCase(user_repo, jwt_service, password_service)

    result = use_case.execute("token", "new-password")

    assert result.password_hash == "new-hash"
    user_repo.update_password.assert_called_once_with(user_id=17, password_hash="new-hash")
