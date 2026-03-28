from __future__ import annotations

from unittest.mock import Mock

from src.backend.use_case.auth.logout_user import LogoutUserUseCase


def test_logout_user_clears_user_session():
    """Проверяем, что LogoutUserUseCase вызывает очистку пользовательской сессии."""
    user_repository = Mock()
    use_case = LogoutUserUseCase(user_repository)

    result = use_case.execute(15)

    assert result is True
    user_repository.clear_user_session.assert_called_once_with(15)
