from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from backend.application.use_cases.auth.request_password_reset import (
    RequestPasswordResetUseCase,
)
from unittest.mock import AsyncMock, Mock

import backend.application.use_cases.auth.request_password_reset as module


@pytest.mark.unit
class TestRequestPasswordResetUseCase:
    """Юнит-тесты сценария запроса сброса пароля."""

    async def test_skips_unknown_user(self, monkeypatch):
        """Что тестируем: ничего не отправляется для неизвестного email.
        Что передаём: get_by_email=None и подмененный Settings.
        Что ожидаем: создание токена и письмо не вызываются, возвращается success.
        """
        monkeypatch.setattr(
            module,
            "Settings",
            SimpleNamespace(password_reset_expire_minutes=30, app_base_url="http://app.local"),
        )
        user_repo = AsyncMock()
        user_repo.get_by_email.return_value = None
        jwt_service = AsyncMock()
        mailer = AsyncMock()
        use_case = RequestPasswordResetUseCase(user_repo, jwt_service, mailer)

        result = await use_case.execute("missing@example.com")

        assert result.ok is True
        jwt_service.create_password_reset_token.assert_not_awaited()
        mailer.send_reset_email.assert_not_awaited()

    async def test_builds_reset_link(self, monkeypatch):
        """Что тестируем: создание токена и корректной ссылки сброса.
        Что передаём: существующего пользователя и переданный base_url.
        Что ожидаем: токен создан с expires_minutes, письмо отправлено со ссылкой.
        """
        monkeypatch.setattr(
            module,
            "Settings",
            SimpleNamespace(password_reset_expire_minutes=30, app_base_url="http://app.local"),
        )
        user_repo = AsyncMock()
        user_repo.get_by_email.return_value = SimpleNamespace(id=7, email="user@example.com")
        jwt_service = Mock()
        jwt_service.create_password_reset_token.return_value = "reset-token"
        mailer = AsyncMock()
        use_case = RequestPasswordResetUseCase(user_repo, jwt_service, mailer)

        result = await use_case.execute("user@example.com", base_url="http://frontend.local/")

        assert result.ok is True
        jwt_service.create_password_reset_token.assert_called_once_with(
            user_id=7, expires_minutes=30
        )
        mailer.send_reset_email.assert_awaited_once_with(
            "user@example.com",
            "http://frontend.local/auth/password-reset/confirm?token=reset-token",
        )