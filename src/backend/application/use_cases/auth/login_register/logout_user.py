"""Сценарий выхода: отзыв токенов аутентификации."""

from __future__ import annotations

import logging

from backend.application.dto import LogoutCommand
from backend.application.interface.services.jwt_service import JWTServiceInterface
from backend.application.interface.services.token_blocklist import TokenBlocklistInterface
from backend.application.use_cases.auth.result import AuthResult

logger = logging.getLogger("anime_epic_moments")


class LogoutUserUseCase:
    """Отозвать access- и refresh-токены, чтобы их нельзя было использовать."""

    def __init__(
        self,
        jwt_service: JWTServiceInterface,
        token_blocklist: TokenBlocklistInterface,
    ) -> None:
        """Собрать сценарий выхода.

        Args:
            jwt_service: Сервис разбора JWT-токенов.
            token_blocklist: Хранилище отозванных токенов.
        """
        self._jwt_service = jwt_service
        self._token_blocklist = token_blocklist

    async def execute(self, command: LogoutCommand) -> AuthResult:
        """Отозвать переданные токены.

        Захват широкий намеренно: выход из сессии не должен зависеть от
        хранилища отозванных токенов. Если отзыв не удался, пользователь всё
        равно получает успешный итог, а случай уходит в лог с контекстом типа
        токена и stack trace.

        Args:
            command: Команда выхода с значениями токенов из cookie.

        Returns:
            AuthResult: Всегда успешный итог с переходом на главную.
        """
        tokens = (
            (str(command.access_token or "").strip(), "access"),
            (str(command.refresh_token or "").strip(), "refresh"),
        )
        for token, expected_type in tokens:
            if not token:
                continue
            try:
                await self._token_blocklist.revoke(
                    token,
                    await self._jwt_service.get_token_ttl_seconds(
                        token, expected_type=expected_type
                    ),
                )
            except Exception:
                logger.warning("token_revoke_failed type=%s", expected_type, exc_info=True)
        return AuthResult.success(redirect_endpoint="index.index")
