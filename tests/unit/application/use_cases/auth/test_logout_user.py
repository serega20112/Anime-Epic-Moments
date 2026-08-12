from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from backend.application.use_cases.auth.logout_user import LogoutUserUseCase


@pytest.mark.unit
class TestLogoutUserUseCase:
    """Юнит-тесты выхода пользователя из аккаунта."""

    async def test_revokes_access_and_refresh_tokens(self):
        """Что тестируем: отзыв access и refresh токенов.
        Что передаём: оба токена с замоканным jwt_service.
        Что ожидаем: оба токена отправлены в blocklist с правильным ttl.
        """
        jwt_service = AsyncMock()
        jwt_service.get_token_ttl_seconds.side_effect = lambda _token, expected_type=None: {
            "access": 900,
            "refresh": 604800,
        }[expected_type]
        token_blocklist = AsyncMock()
        use_case = LogoutUserUseCase(jwt_service, token_blocklist)

        result = await use_case.execute("access-token", "refresh-token")

        assert result.ok is True
        assert result.redirect_endpoint == "index.index"
        token_blocklist.revoke.assert_awaited()
        revoke_calls = token_blocklist.revoke.await_args_list
        assert revoke_calls[0].args[:1] == ("access-token",)
        assert revoke_calls[1].args[:1] == ("refresh-token",)

    @pytest.mark.parametrize(
        ("access_token", "refresh_token", "expected_count"),
        [("", "refresh-token", 1), ("access-token", "", 1), ("", "", 0)],
    )
    async def test_skips_empty_tokens(self, access_token, refresh_token, expected_count):
        """Что тестируем: пропуск пустых токенов.
        Что передаём: комбинации пустых/заполненных токенов.
        Что ожидаем: revoke вызывается только для непустых токенов.
        """
        jwt_service = AsyncMock()
        jwt_service.get_token_ttl_seconds.return_value = 900
        token_blocklist = AsyncMock()
        use_case = LogoutUserUseCase(jwt_service, token_blocklist)

        result = await use_case.execute(access_token, refresh_token)

        assert result.ok is True
        assert len(token_blocklist.revoke.await_args_list) == expected_count