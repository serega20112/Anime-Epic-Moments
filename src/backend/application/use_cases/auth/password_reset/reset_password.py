"""Сброс пароля по одноразовому токену."""

from __future__ import annotations

from backend.application.dto import ConfirmPasswordResetCommand
from backend.application.interface.repositories.user_repository import UserRepository
from backend.application.interface.services import PasswordServiceInterface
from backend.application.interface.services.jwt_service import JWTServiceInterface
from backend.application.interface.services.token_blocklist import TokenBlocklistInterface
from backend.application.interface.unit_of_work import UnitOfWorkInterface
from backend.application.use_cases.auth.result import AuthResult
from backend.domain.exceptions import InvalidTokenError

INVALID_TOKEN_MESSAGE = "Ссылка для сброса пароля недействительна или устарела"
USED_TOKEN_MESSAGE = "Ссылка для сброса пароля уже использована"
USER_NOT_FOUND_MESSAGE = "Пользователь не найден"
PASSWORD_UPDATED_MESSAGE = "Пароль обновлен. Теперь можно войти."
CONFIRM_ENDPOINT = "auth.password_reset_confirm_page"


class ResetPasswordUseCase:
    """Сбрасывает пароль пользователя по валидному токену."""

    def __init__(
        self,
        unit_of_work: UnitOfWorkInterface,
        jwt_service: JWTServiceInterface,
        password_service: PasswordServiceInterface,
        token_blocklist: TokenBlocklistInterface,
    ) -> None:
        """Инициализирует сценарий сброса пароля.

        Args:
            unit_of_work: Граница транзакции записи нового пароля.
            jwt_service: Сервис JWT-токенов.
            password_service: Сервис хеширования паролей.
            token_blocklist: Хранилище блокированных токенов.
        """
        self._unit_of_work = unit_of_work
        self._jwt_service = jwt_service
        self._password_service = password_service
        self._token_blocklist = token_blocklist

    async def execute(self, command: ConfirmPasswordResetCommand) -> AuthResult:
        """Сбрасывает пароль пользователя внутри транзакции.

        Args:
            command: Токен из письма и новый пароль.

        Returns:
            AuthResult: Success на страницу логина или failure на страницу
                подтверждения.
        """
        token = str(command.token or "").strip()
        if not token:
            return AuthResult.failure(INVALID_TOKEN_MESSAGE, CONFIRM_ENDPOINT)
        try:
            user_id = await self._jwt_service.decode_password_reset_token(token)
        except InvalidTokenError:
            return AuthResult.failure(INVALID_TOKEN_MESSAGE, CONFIRM_ENDPOINT)

        password_hash = await self._password_service.hash_password(command.password)
        async with self._unit_of_work as uow:
            repository = uow.repository(UserRepository)
            user = await repository.get_by_id(user_id)
            if user is None:
                return AuthResult.failure(USER_NOT_FOUND_MESSAGE, CONFIRM_ENDPOINT)
            ttl_seconds = await self._jwt_service.get_token_ttl_seconds(
                token, expected_type="password_reset"
            )
            if not await self._token_blocklist.consume(token, ttl_seconds):
                return AuthResult.failure(USED_TOKEN_MESSAGE, CONFIRM_ENDPOINT)
            await repository.update_password(user_id=user_id, password_hash=password_hash)
        return AuthResult.success(
            message=PASSWORD_UPDATED_MESSAGE,
            redirect_endpoint="auth.login_page",
        )
