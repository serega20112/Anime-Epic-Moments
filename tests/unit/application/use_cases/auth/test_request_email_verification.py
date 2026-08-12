from __future__ import annotations

from unittest.mock import AsyncMock, Mock

import pytest

from backend.application.use_cases.auth.request_email_verification import (
    RequestEmailVerificationUseCase,
)
from backend.application.use_cases.auth.result import AuthResult
from backend.domain import PendingEmailVerification


@pytest.mark.unit
class TestRequestEmailVerification:
    """Юнит-тесты запроса кода подтверждения email при регистрации."""

    async def test_rejects_duplicate_email(self):
        """Что тестируем: отказ при уже зарегистрированном email.
        Что передаём: get_by_email возвращает существующего пользователя.
        Что ожидаем: AuthResult.failure и mailer не вызывается.
        """
        user_repo = AsyncMock()
        user_repo.get_by_email.return_value = object()
        mailer = AsyncMock()
        use_case = RequestEmailVerificationUseCase(user_repo, Mock(), AsyncMock(), mailer)

        result = await use_case.execute(
            email="user@example.com", password="password123", username="tester"
        )

        assert result.ok is False
        assert result.error_endpoint == "auth.register_page"
        mailer.send_verification_code.assert_not_awaited()

    @pytest.mark.parametrize(
        ("email", "username", "theme", "expected_theme"),
        [
            ("User@Example.COM", "tester", "dark", "dark"),
            ("rose@example.com", "rose-user", "rose", "rose"),
            (" user@example.com ", "  tester  ", "unknown", "neon"),
        ],
    )
    async def test_normalizes_hashes_saves_and_sends_code(
            self, email, username, theme, expected_theme, monkeypatch
    ):
        """Что тестируем: нормализацию данных, хеширование, сохранение и отправку кода.
        Что передаём: вариации email/username/theme.
        Что ожидаем: AuthResult.success с redirect_email и сохраненный PendingEmailVerification.
        """
        user_repo = AsyncMock()
        user_repo.get_by_email.return_value = None
        password_service = Mock()
        password_service.hash_password.return_value = "hashed-password"
        verification_store = AsyncMock()
        verification_store.save.side_effect = lambda payload: payload
        mailer = AsyncMock()
        use_case = RequestEmailVerificationUseCase(
            user_repo, password_service, verification_store, mailer
        )
        monkeypatch.setattr(use_case, "_generate_code", lambda: "123456")

        result = await use_case.execute(
            email, "password123", username, theme=theme
        )

        normalized_email = email.strip().lower()
        assert isinstance(result, AuthResult)
        assert result.ok is True
        assert result.redirect_endpoint == "auth.verify_email_page"
        assert result.redirect_email == normalized_email
        password_service.hash_password.assert_called_once_with("password123")
        saved_payload = verification_store.save.call_args.args[0]
        assert isinstance(saved_payload, PendingEmailVerification)
        assert saved_payload.email == normalized_email
        assert saved_payload.code == "123456"
        assert saved_payload.theme == expected_theme
        mailer.send_verification_code.assert_awaited_with(
            normalized_email, "123456", theme=expected_theme
        )