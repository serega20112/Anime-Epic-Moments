from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from backend.application.use_cases.auth.verification.verify_email import VerifyEmailUseCase
from backend.domain import PendingEmailVerification, User


@pytest.mark.unit
class TestVerifyEmailUseCase:
    """Юнит-тесты подтверждения email кодом и создания пользователя."""

    async def test_returns_failure_when_payload_missing(self):
        """Что тестируем: отказ при отсутствии ожидающей регистрации.
        Что передаём: verification_store.get возвращает None.
        Что ожидаем: AuthResult.failure и user_repo.add не вызывается.
        """
        verification_store = AsyncMock()
        verification_store.get.return_value = None
        user_repo = AsyncMock()
        use_case = VerifyEmailUseCase(user_repo, verification_store, AsyncMock())

        result = await use_case.execute(email=" User@Example.com ", code="123456")

        assert result.ok is False
        assert result.error_endpoint == "auth.verify_email_page"
        assert result.redirect_email == "user@example.com"
        user_repo.add.assert_not_awaited()

    @pytest.mark.parametrize(
        ("stored_code", "submitted_code", "expected_ok"),
        [
            ("123456", "123456", True),
            ("123456", "654321", False),
            ("123456", "", False),
        ],
    )
    async def test_accepts_code_only_when_it_matches(
        self, stored_code, submitted_code, expected_ok
    ):
        """Что тестируем: сверку кода подтверждения.
        Что передаём: пары значений сохраненного и введенного кода.
        Что ожидаем: успех только при совпадении кодов.
        """
        payload = PendingEmailVerification(
            email="user@example.com",
            username="tester",
            password_hash="hashed-password",
            code=stored_code,
            theme="neon",
        )
        verification_store = AsyncMock()
        verification_store.get.return_value = payload
        user_repo = AsyncMock()
        user_repo.get_by_email.return_value = None
        user_repo.add.side_effect = lambda user: SimpleNamespace(
            id=1, email=user.email, username=user.username, password_hash=user.password_hash
        )
        use_case = VerifyEmailUseCase(user_repo, verification_store, AsyncMock())

        result = await use_case.execute(email="user@example.com", code=submitted_code)

        assert result.ok is expected_ok
        if expected_ok:
            created_user = user_repo.add.call_args.args[0]
            assert created_user.email == "user@example.com"
            assert created_user.username == "tester"
            assert created_user.password_hash == "hashed-password"
            assert result.data.id == 1
            assert result.redirect_endpoint == "index.index"
            verification_store.delete.assert_awaited_with("user@example.com")
        else:
            user_repo.add.assert_not_awaited()

    @pytest.mark.parametrize("existing_email", ["user@example.com", None])
    async def test_reuses_existing_email(self, existing_email):
        """Что тестируем: обработку повторной регистрации email.
        Что передаём: get_by_email возвращает/не возвращает пользователя.
        Что ожидаем: существующий email не создает нового пользователя, а возвращает failure.
        """
        payload = PendingEmailVerification(
            email="user@example.com",
            username="tester",
            password_hash="hashed-password",
            code="123456",
            theme="neon",
        )
        verification_store = AsyncMock()
        verification_store.get.return_value = payload
        user_repo = AsyncMock()
        user_repo.get_by_email.return_value = existing_email is not None and User(
            email="user@example.com", username="other", password_hash="x"
        )
        use_case = VerifyEmailUseCase(user_repo, verification_store, AsyncMock())

        result = await use_case.execute(email="user@example.com", code="123456")

        if existing_email is not None:
            assert result.ok is False
            user_repo.add.assert_not_awaited()
        else:
            assert result.ok is True
            user_repo.add.assert_awaited()
