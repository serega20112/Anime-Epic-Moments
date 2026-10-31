"""Сценарий продления сессии с ротацией токенов."""

from __future__ import annotations

from backend.application.dto import RefreshSessionCommand
from backend.application.interface.repositories.user_repository import UserRepository
from backend.application.interface.services.jwt_service import JWTServiceInterface
from backend.application.interface.services.token_blocklist import TokenBlocklistInterface
from backend.application.interface.unit_of_work import UnitOfWorkInterface
from backend.application.use_cases.auth.result import AuthResult
from backend.domain import User
from backend.domain.exceptions import InvalidTokenError

USER_MISSING_MESSAGE = "Пользователь не найден"
REFRESH_FAILURE_ENDPOINT = "auth.refresh_session"


class RefreshSessionUseCase:
    """Проверить refresh-токен и вернуть владельца с новой парой токенов.

    Пустые, отозванные и повреждённые токены отклоняются, а использованный
    refresh-токен сразу попадает в список отозванных, поэтому повторный обмен
    того же значения невозможен.
    """

    def __init__(
        self,
        jwt_service: JWTServiceInterface,
        token_blocklist: TokenBlocklistInterface,
        unit_of_work: UnitOfWorkInterface,
    ) -> None:
        """Собрать сценарий продления сессии.

        Args:
            jwt_service: Сервис разбора JWT-токенов.
            token_blocklist: Хранилище отозванных токенов.
            unit_of_work: Граница транзакции чтения пользователя.
        """
        self._jwt_service = jwt_service
        self._token_blocklist = token_blocklist
        self._unit_of_work = unit_of_work

    async def execute(self, command: RefreshSessionCommand) -> AuthResult:
        """Обменять refresh-токен на новую пару токенов.

        Args:
            command: Команда продления со значением refresh-токена.

        Returns:
            AuthResult: Аутентифицированный пользователь либо отказ.
        """
        token = str(command.refresh_token or "").strip()
        if not token:
            return AuthResult.failure("auth_required", REFRESH_FAILURE_ENDPOINT)
        try:
            user_id = await self._jwt_service.decode_refresh_token(token)
        except InvalidTokenError:
            return AuthResult.failure("invalid_token", REFRESH_FAILURE_ENDPOINT)
        ttl_seconds = await self._jwt_service.get_token_ttl_seconds(token, expected_type="refresh")
        if not await self._token_blocklist.consume(token, ttl_seconds):
            return AuthResult.failure("invalid_token", REFRESH_FAILURE_ENDPOINT)
        user = await self._load_user(user_id)
        if user is None:
            return AuthResult.failure(USER_MISSING_MESSAGE, REFRESH_FAILURE_ENDPOINT)
        return AuthResult.success(data=user)

    async def _load_user(self, user_id: int) -> User | None:
        """Прочитать владельца токена, чтобы не продлевать удалённый аккаунт.

        Args:
            user_id: Идентификатор пользователя из refresh-токена.

        Returns:
            User | None: Найденный пользователь либо None.
        """
        async with self._unit_of_work as uow:
            repository = uow.repository(UserRepository)
            return await repository.get_by_id(user_id)
