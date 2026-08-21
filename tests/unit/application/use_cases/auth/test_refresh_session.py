from __future__ import annotations

from unittest.mock import AsyncMock, Mock

import jwt

from backend.application.use_cases.auth.login_register.refresh_session import RefreshSessionUseCase


def _build(jwt_service=None, token_blocklist=None):
    use_case = RefreshSessionUseCase(
        jwt_service=jwt_service or AsyncMock(),
        token_blocklist=token_blocklist or AsyncMock(),
    )
    return use_case


class TestRefreshSessionUseCase:
    async def test_rejects_blank_token(self):
        use_case = _build()
        result = await use_case.execute("   ")
        assert result.ok is False
        assert result.error_message == "auth_required"

    async def test_rejects_already_consumed_token(self):
        blocklist = AsyncMock()
        blocklist.consume = AsyncMock(return_value=False)
        use_case = _build(token_blocklist=blocklist)
        result = await use_case.execute("used-token")
        assert result.ok is False
        assert result.error_message == "invalid_token"

    async def test_rejects_malformed_token(self):
        jwt_service = Mock()
        jwt_service.decode_refresh_token.side_effect = jwt.InvalidTokenError("bad token")
        use_case = _build(jwt_service=jwt_service)
        result = await use_case.execute("bad-token")
        assert result.ok is False
        assert result.error_message == "invalid_token"

    async def test_rotates_token_on_success(self):
        jwt_service = Mock()
        jwt_service.decode_refresh_token = AsyncMock(return_value=42)
        jwt_service.get_token_ttl_seconds = AsyncMock(return_value=3600)
        blocklist = AsyncMock()
        blocklist.consume = AsyncMock(return_value=True)
        use_case = _build(jwt_service=jwt_service, token_blocklist=blocklist)

        result = await use_case.execute("valid-token")

        assert result.ok is True
        assert result.data == 42
        blocklist.consume.assert_awaited_once_with("valid-token", 3600)
