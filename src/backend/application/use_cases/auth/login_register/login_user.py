"""Сценарий аутентификации пользователя по email и паролю."""

from __future__ import annotations

from backend.application.dto import LoginCommand
from backend.application.interface.services import (
    AccountLockServiceInterface,
    PasswordServiceInterface,
)
from backend.application.interface.unit_of_work import UnitOfWorkInterface
from backend.application.use_cases.auth.result import AuthResult
from backend.application.use_cases.auth.user_lookup import find_user_by_email
from backend.domain.policies.user_credentials_policy import normalize_email

ACCOUNT_LOCKED_MESSAGE = (
    "Аккаунт временно заблокирован из-за множества неудачных попыток входа. Попробуйте позже."
)
INVALID_CREDENTIALS_MESSAGE = "Неверный email или пароль"
DUMMY_PASSWORD_HASH = "$2b$12$YkpE4gT/crtJTugOQ0Uh5ObWVyl1NJXIXc/xc4MbchXOi4R2JXns2"


def welcome_message(username: str) -> str:
    """Формирует приветственное сообщение после успешного входа.

    Args:
        username: Имя пользователя.

    Returns:
        str: Текст приветствия.
    """
    return f"Добро пожаловать, {username}!"


class LoginUserUseCase:
    """Проверяет учётные данные и возвращает аутентифицированного пользователя.

    Применяет блокировку аккаунта: полностью заблокированные аккаунты
    отклоняются до любой проверки учётных данных, неудачные попытки
    регистрируются, а успешный вход сбрасывает счётчик попыток.
    """

    def __init__(
        self,
        unit_of_work: UnitOfWorkInterface,
        password_service: PasswordServiceInterface,
        account_lock_service: AccountLockServiceInterface,
    ) -> None:
        """Инициализирует сценарий входа.

        Args:
            unit_of_work: Граница транзакции чтения пользователя.
            password_service: Сервис хеширования и проверки паролей.
            account_lock_service: Сервис блокировки аккаунта по числу попыток.
        """
        self._unit_of_work = unit_of_work
        self._password_service = password_service
        self._account_lock_service = account_lock_service

    async def execute(self, command: LoginCommand) -> AuthResult:
        """Аутентифицирует пользователя по email и паролю.

        Args:
            command: Данные формы входа.

        Returns:
            AuthResult: Успех с пользователем или неудача с информацией о редиректе.
        """
        email = normalize_email(command.email)
        locked = await self._ensure_not_locked(email)
        if locked is not None:
            return locked
        user = await find_user_by_email(self._unit_of_work, email)
        stored_hash = user.password_hash if user else DUMMY_PASSWORD_HASH
        password_matches = await self._password_service.verify_password(
            command.password, stored_hash
        )
        if not user or not password_matches:
            await self._record_failure(email)
            return AuthResult.failure(INVALID_CREDENTIALS_MESSAGE, "auth.login_page")
        await self._reset_on_success(email)
        return AuthResult.success(
            data=user,
            message=welcome_message(user.username),
            redirect_endpoint="index.index",
        )

    async def _ensure_not_locked(self, email: str) -> AuthResult | None:
        """Вернуть отказ, если аккаунт заблокирован.

        Args:
            email: Нормализованный адрес почты.

        Returns:
            AuthResult | None: Результат отказа либо None для разблокированного аккаунта.
        """
        is_locked, _unlock_at = await self._account_lock_service.is_account_locked(email)
        if is_locked:
            return AuthResult.failure(ACCOUNT_LOCKED_MESSAGE, "auth.login_page")
        return None

    async def _record_failure(self, email: str) -> None:
        """Записать неудачную попытку входа.

        Args:
            email: Нормализованный адрес почты.
        """
        await self._account_lock_service.record_failed_attempt(email)

    async def _reset_on_success(self, email: str) -> None:
        """Сбросить блокировку после успешного входа.

        Args:
            email: Нормализованный адрес почты.
        """
        await self._account_lock_service.unlock_account(email)
