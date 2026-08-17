from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import jwt
import pytest

from backend.application.use_cases.auth.reset_password import ResetPasswordUseCase


def _blocklist():
    blocklist = Mock()
    blocklist.consume = AsyncMock(return_value=True)
    return blocklist


@pytest.mark.unit
class TestResetPasswordUseCase:
    """Юнит-тесты сценария сброса пароля через токен."""

    async def test_rejects_invalid_token(self):
        """Что тестируем: отклонение неверного или просроченного токена.
        Что передаём: decode_password_reset_token бросает PyJWTError.
        Что ожидаем: результат failure с указанием confirm-страницы, пароль не обновляется.
        """
        user_repo = AsyncMock()
        jwt_service = Mock()
        jwt_service.decode_password_reset_token.side_effect = jwt.InvalidTokenError("bad token")
        password_service = Mock()
        use_case = ResetPasswordUseCase(
            user_repo, jwt_service, password_service, _blocklist(), AsyncMock()
        )

        result = await use_case.execute("bad-token", "new-password")

        assert result.ok is False
        assert result.error_endpoint == "auth.password_reset_confirm_page"
        user_repo.update_password.assert_not_awaited()

    async def test_rejects_revoked_token(self):
        """Что тестируем: отклонение уже использованного токена.
        Что передаём: token_blocklist.consume возвращает False.
        Что ожидаем: результат failure, пароль не обновляется.
        """
        user_repo = AsyncMock()
        jwt_service = AsyncMock()
        password_service = AsyncMock()
        blocklist = Mock()
        blocklist.consume = AsyncMock(return_value=False)
        use_case = ResetPasswordUseCase(
            user_repo, jwt_service, password_service, blocklist, AsyncMock()
        )

        result = await use_case.execute("token", "new-password")

        assert result.ok is False
        user_repo.update_password.assert_not_awaited()

    async def test_rejects_missing_user(self):
        """Что тестируем: отклонение токена пользователя, которого нет в репозитории.
        Что передаём: decode возвращает id, get_by_id=None.
        Что ожидаем: результат failure, пароль не обновляется.
        """
        user_repo = AsyncMock()
        user_repo.get_by_id.return_value = None
        jwt_service = AsyncMock()
        jwt_service.decode_password_reset_token = AsyncMock(return_value=17)
        use_case = ResetPasswordUseCase(user_repo, jwt_service, Mock(), _blocklist(), AsyncMock())

        result = await use_case.execute("token", "new-password")

        assert result.ok is False
        user_repo.update_password.assert_not_awaited()

    async def test_hashes_and_persists_new_password(self):
        """Что тестируем: хеширование и сохранение нового пароля.
        Что передаём: валидный токен и существующего пользователя.
        Что ожидаем: пароль захеширован и сохранен, возвращается success.
        """
        user_repo = AsyncMock()
        user_repo.get_by_id.return_value = SimpleNamespace(id=17)
        jwt_service = AsyncMock()
        jwt_service.decode_password_reset_token = AsyncMock(return_value=17)
        jwt_service.get_token_ttl_seconds = AsyncMock(return_value=1800)
        password_service = AsyncMock()
        password_service.hash_password.return_value = "new-hash"
        blocklist = _blocklist()
        use_case = ResetPasswordUseCase(
            user_repo, jwt_service, password_service, blocklist, AsyncMock()
        )

        result = await use_case.execute("token", "new-password")

        assert result.ok is True
        assert result.redirect_endpoint == "auth.login_page"
        password_service.hash_password.assert_awaited_once_with("new-password")
        user_repo.update_password.assert_awaited_once_with(user_id=17, password_hash="new-hash")
        blocklist.consume.assert_awaited_once()
