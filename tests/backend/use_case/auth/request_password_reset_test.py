from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import Mock

from src.backend.use_case.auth import request_password_reset as request_password_reset_module
from src.backend.use_case.auth.request_password_reset import RequestPasswordResetUseCase


def test_request_password_reset_skips_unknown_user(monkeypatch):
    """Проверяем, что RequestPasswordResetUseCase ничего не отправляет для неизвестного email."""
    monkeypatch.setattr(
        request_password_reset_module,
        "Settings",
        SimpleNamespace(password_reset_expire_minutes=30, app_base_url="http://app.local"),
    )
    user_repo = Mock()
    user_repo.get_by_email.return_value = None
    jwt_service = Mock()
    mailer = Mock()
    use_case = RequestPasswordResetUseCase(user_repo, jwt_service, mailer)

    use_case.execute("missing@example.com")

    jwt_service.create_password_reset_token.assert_not_called()
    mailer.send_reset_email.assert_not_called()


def test_request_password_reset_builds_reset_link(monkeypatch):
    """Проверяем, что RequestPasswordResetUseCase создает токен и отправляет корректную ссылку сброса."""
    monkeypatch.setattr(
        request_password_reset_module,
        "Settings",
        SimpleNamespace(password_reset_expire_minutes=30, app_base_url="http://app.local"),
    )
    user_repo = Mock()
    user_repo.get_by_email.return_value = SimpleNamespace(id=7, email="user@example.com")
    jwt_service = Mock()
    jwt_service.create_password_reset_token.return_value = "reset-token"
    mailer = Mock()
    use_case = RequestPasswordResetUseCase(user_repo, jwt_service, mailer)

    use_case.execute("user@example.com", base_url="http://frontend.local/")

    jwt_service.create_password_reset_token.assert_called_once_with(user_id=7, expires_minutes=30)
    mailer.send_reset_email.assert_called_once_with(
        "user@example.com",
        "http://frontend.local/auth/password-reset/confirm?token=reset-token",
    )
