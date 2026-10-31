from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from backend.application.dto import LogoutCommand
from backend.application.use_cases.auth.login_register.logout_user import LogoutUserUseCase


def _use_case() -> tuple:
    """Собрать сценарий выхода с двойниками JWT-сервиса и блока токенов."""
    jwt_service = AsyncMock()
    jwt_service.get_token_ttl_seconds.return_value = 60
    blocklist = AsyncMock()
    return LogoutUserUseCase(jwt_service, blocklist), jwt_service, blocklist


@pytest.mark.unit
class TestLogoutUserUseCase:
    """Юнит-тесты отзыва токенов при выходе."""

    async def test_revokes_access_and_refresh_tokens(self):
        """Что тестируем: отзыв обеих пар токенов.
        Что передаём: непустые access и refresh токены.
        Что ожидаем: каждый токен отозван со своим сроком жизни.
        """
        use_case, jwt_service, blocklist = _use_case()

        result = await use_case.execute(
            LogoutCommand(access_token="access-token", refresh_token="refresh-token")
        )

        assert result.ok is True
        assert result.redirect_endpoint == "index.index"
        assert jwt_service.get_token_ttl_seconds.await_count == 2
        assert {call.args[0] for call in blocklist.revoke.await_args_list} == {
            "access-token",
            "refresh-token",
        }

    @pytest.mark.parametrize(
        ("access_token", "refresh_token", "expected_calls"),
        [("", "refresh-token", 1), ("access-token", "", 1), ("  ", "", 0)],
    )
    async def test_skips_empty_tokens(self, access_token, refresh_token, expected_calls):
        """Что тестируем: пропуск пустых токенов.
        Что передаём: пустую строку в одном из полей команды.
        Что ожидаем: отозвано ровно столько токенов, сколько передано.
        """
        use_case, _jwt_service, blocklist = _use_case()

        result = await use_case.execute(
            LogoutCommand(access_token=access_token, refresh_token=refresh_token)
        )

        assert result.ok is True
        assert blocklist.revoke.await_count == expected_calls

    async def test_completes_logout_when_revoking_fails(self):
        """Что тестируем: устойчивость выхода к сбою хранилища токенов.
        Что передаём: блок-лист бросает исключение.
        Что ожидаем: выход всё равно завершён успехом.
        """
        use_case, _jwt_service, blocklist = _use_case()
        blocklist.revoke.side_effect = RuntimeError("redis недоступен")

        result = await use_case.execute(
            LogoutCommand(access_token="access-token", refresh_token="")
        )

        assert result.ok is True
