from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from backend.application.dto import RegisterCommand
from backend.application.use_cases.auth.login_register.register_user import (
    EmailAlreadyExistsError,
    RegisterUserUseCase,
)
from tests.support.fakes import FakeUnitOfWork


def _command(**overrides) -> RegisterCommand:
    """Собрать команду регистрации с переопределёнными полями."""
    fields = {
        "email": "user@example.com",
        "password": "secret-password",
        "username": "tester",
        "theme": "neon",
    }
    fields.update(overrides)
    return RegisterCommand(**fields)


def _use_case(repository: AsyncMock, password_hash: str = "hashed") -> tuple:
    """Собрать сценарий регистрации с двойниками репозитория и хеширования."""
    password_service = AsyncMock()
    password_service.hash_password.return_value = password_hash
    uow = FakeUnitOfWork(UserRepository=repository)
    return RegisterUserUseCase(uow, password_service), uow, repository, password_service


@pytest.mark.unit
class TestRegisterUserUseCase:
    """Юнит-тесты регистрации нового пользователя."""

    async def test_hashes_password_and_saves_user(self):
        """Что тестируем: создание пользователя с хешем пароля.
        Что передаём: корректную команду регистрации.
        Что ожидаем: пользователь сохранён, пароль не попал в базу в открытом виде.
        """
        repository = AsyncMock()
        repository.get_by_email.return_value = None
        repository.add.side_effect = lambda user: user
        use_case, uow, _repository, password_service = _use_case(repository)

        user = await use_case.execute(_command())

        assert user.email == "user@example.com"
        assert user.password_hash == "hashed"
        assert uow.commits == 1
        password_service.hash_password.assert_awaited_once_with("secret-password")
        saved = repository.add.await_args.args[0]
        assert saved.username == "tester"

    async def test_rejects_duplicate_email(self):
        """Что тестируем: отказ при занятом адресе почты.
        Что передаём: репозиторий возвращает существующего пользователя.
        Что ожидаем: EmailAlreadyExistsError, пользователь не сохранён, транзакция откачена.
        """
        repository = AsyncMock()
        repository.get_by_email.return_value = object()
        use_case, uow, _repository, _passwords = _use_case(repository)

        with pytest.raises(EmailAlreadyExistsError):
            await use_case.execute(_command())

        repository.add.assert_not_awaited()
        assert uow.rollbacks == 1
