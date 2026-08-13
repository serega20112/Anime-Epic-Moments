from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from backend.application.use_cases.auth.register_user import (
    EmailAlreadyExistsError,
    RegisterUserUseCase,
)


@pytest.mark.unit
class TestRegisterUserUseCase:
    """Юнит-тесты сценария регистрации нового пользователя."""

    async def test_rejects_duplicate_email(self):
        """Что тестируем: отказ при уже занятом email.
        Что передаём: get_by_email возвращает существующего пользователя.
        Что ожидаем: возбуждается EmailAlreadyExistsError, add не вызывается.
        """
        user_repo = AsyncMock()
        user_repo.get_by_email.return_value = object()
        use_case = RegisterUserUseCase(user_repo, Mock(), AsyncMock())

        with pytest.raises(EmailAlreadyExistsError):
            await use_case.execute(email="user@example.com", password="password", username="tester")

        user_repo.add.assert_not_awaited()

    async def test_hashes_password_and_saves_user(self):
        """Что тестируем: хеширование пароля и сохранение пользователя.
        Что передаём: свободный email и корректные username/password.
        Что ожидаем: add получает пользователя с хешем и полями, возвращается сохраненный объект.
        """
        user_repo = AsyncMock()
        user_repo.get_by_email.return_value = None
        user_repo.add.side_effect = lambda user: SimpleNamespace(
            id=1, email=user.email, username=user.username, password_hash=user.password_hash
        )
        password_service = AsyncMock()
        password_service.hash_password.return_value = "hashed-password"
        use_case = RegisterUserUseCase(user_repo, password_service, AsyncMock())

        result = await use_case.execute(
            email="user@example.com", password="password", username="tester"
        )

        password_service.hash_password.assert_called_once_with("password")
        saved_user = user_repo.add.call_args.args[0]
        assert saved_user.email == "user@example.com"
        assert saved_user.username == "tester"
        assert saved_user.password_hash == "hashed-password"
        assert result.id == 1