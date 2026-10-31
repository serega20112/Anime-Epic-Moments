from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from backend.application.dto import RefreshSessionCommand
from backend.application.use_cases.auth.login_register.refresh_session import RefreshSessionUseCase
from backend.domain.exceptions import InvalidTokenError
from tests.support.fakes import FakeUnitOfWork


def _user(user_id: int = 7) -> SimpleNamespace:
    """Собрать владельца токена для двойника репозитория."""
    return SimpleNamespace(id=user_id, username="tester", email="user@example.com")


def _use_case(
    *,
    decoded_user_id: int | None = 7,
    decode_error: Exception | None = None,
    consumed: bool = True,
    user_exists: bool = True,
) -> tuple:
    """Собрать сценарий продления сессии с двойниками JWT, блок-листа и транзакции."""
    jwt_service = AsyncMock()
    jwt_service.get_token_ttl_seconds.return_value = 120
    if decode_error is not None:
        jwt_service.decode_refresh_token.side_effect = decode_error
    else:
        jwt_service.decode_refresh_token.return_value = decoded_user_id
    blocklist = AsyncMock()
    blocklist.consume.return_value = consumed
    user_repo = AsyncMock()
    user_repo.get_by_id.return_value = _user() if user_exists else None
    return (
        RefreshSessionUseCase(jwt_service, blocklist, FakeUnitOfWork(UserRepository=user_repo)),
        jwt_service,
        blocklist,
    )


@pytest.mark.unit
class TestRefreshSessionUseCase:
    """Юнит-тесты продления сессии с ротацией refresh-токена."""

    async def test_rotates_token_on_success(self):
        """Что тестируем: успешный обмен refresh-токена на владельца.
        Что передаём: действующий непустой токен.
        Что ожидаем: токен однократно потреблён, возвращён пользователь токена.
        """
        use_case, _jwt_service, blocklist = _use_case()

        result = await use_case.execute(RefreshSessionCommand(refresh_token="refresh-token"))

        assert result.ok is True
        assert result.data.id == 7
        blocklist.consume.assert_awaited_once_with("refresh-token", 120)

    async def test_rejects_owner_absent_in_database(self):
        """Что тестируем: продление токена удалённого аккаунта.
        Что передаём: репозиторий возвращает None для идентификатора из токена.
        Что ожидаем: отказ с текстом об отсутствии пользователя.
        """
        use_case, _jwt_service, _blocklist = _use_case(user_exists=False)

        result = await use_case.execute(RefreshSessionCommand(refresh_token="refresh-token"))

        assert result.ok is False
        assert result.error_message == "Пользователь не найден"

    async def test_rejects_blank_token(self):
        """Что тестируем: отказ на пустом токене.
        Что передаём: команду из пробелов.
        Что ожидаем: отказ auth_required без обращения к сервисам.
        """
        use_case, jwt_service, blocklist = _use_case()

        result = await use_case.execute(RefreshSessionCommand(refresh_token="   "))

        assert result.ok is False
        assert result.error_message == "auth_required"
        jwt_service.decode_refresh_token.assert_not_awaited()
        blocklist.consume.assert_not_awaited()

    async def test_rejects_malformed_token(self):
        """Что тестируем: отказ на повреждённом токене.
        Что передаём: JWT-сервис бросает доменный InvalidTokenError.
        Что ожидаем: отказ invalid_token, токен не потребляется.
        """
        use_case, _jwt_service, blocklist = _use_case(decode_error=InvalidTokenError("bad"))

        result = await use_case.execute(RefreshSessionCommand(refresh_token="broken"))

        assert result.ok is False
        assert result.error_message == "invalid_token"
        blocklist.consume.assert_not_awaited()

    async def test_rejects_already_consumed_token(self):
        """Что тестируем: повторное использование одного токена.
        Что передаём: блок-лист отвечает, что токен уже потреблён.
        Что ожидаем: отказ invalid_token.
        """
        use_case, _jwt_service, _blocklist = _use_case(consumed=False)

        result = await use_case.execute(RefreshSessionCommand(refresh_token="refresh-token"))

        assert result.ok is False
        assert result.error_message == "invalid_token"
        assert result.error_endpoint == "auth.refresh_session"
