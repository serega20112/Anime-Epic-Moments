"""Генерация и проверка JWT-токенов приложения.

Реализация порта :class:`JWTServiceInterface` на библиотеке PyJWT: токен
несёт идентификатор пользователя и служебный тип, чтобы access-, refresh- и
reset-токены нельзя было взаимно подставить друг друга.

Отказ разбора превращается в доменный :class:`InvalidTokenError`: сценарии и
представление ловят его, не зная, какой библиотекой токен был подписан.
"""

from datetime import UTC, datetime, timedelta

import jwt

from backend.application.interface.services.jwt_service import JWTServiceInterface
from backend.config import Settings
from backend.domain.exceptions import InvalidTokenError

ALGORITHM = "HS256"
ACCESS_TOKEN_TYPE = "access"
REFRESH_TOKEN_TYPE = "refresh"
PASSWORD_RESET_TOKEN_TYPE = "password_reset"
INVALID_TOKEN_TYPE_MESSAGE = "Invalid token type"


class JWTService(JWTServiceInterface):
    """Создаёт и проверяет JWT-токены пользователя."""

    async def create_token(self, user_id: int) -> str:
        """Создать access-токен (устаревшее имя публичного метода).

        Args:
            user_id: Идентификатор пользователя.

        Returns:
            str: Закодированный access-токен.
        """
        return await self.create_access_token(user_id)

    async def create_access_token(self, user_id: int) -> str:
        """Создать access-токен с ограничением из настроек.

        Args:
            user_id: Идентификатор пользователя.

        Returns:
            str: Закодированный access-токен.
        """
        return await self._create_typed_token(
            user_id=user_id,
            token_type=ACCESS_TOKEN_TYPE,
            expires_delta=timedelta(minutes=Settings.access_token_expire_minutes),
        )

    async def create_refresh_token(self, user_id: int) -> str:
        """Создать refresh-токен на срок из настроек.

        Args:
            user_id: Идентификатор пользователя.

        Returns:
            str: Закодированный refresh-токен.
        """
        return await self._create_typed_token(
            user_id=user_id,
            token_type=REFRESH_TOKEN_TYPE,
            expires_delta=timedelta(days=Settings.refresh_token_expire_days),
        )

    async def decode_token(self, token: str) -> int:
        """Расшифровать access-токен и вернуть идентификатор пользователя.

        Args:
            token: Закодированный access-токен.

        Returns:
            int: Идентификатор пользователя.

        Raises:
            InvalidTokenError: Токен недействителен, истёк либо имеет
                другой служебный тип.
        """
        return await self._decode_typed_token(token=token, expected_type=ACCESS_TOKEN_TYPE)

    async def decode_refresh_token(self, token: str) -> int:
        """Расшифровать refresh-токен и вернуть идентификатор пользователя.

        Args:
            token: Закодированный refresh-токен.

        Returns:
            int: Идентификатор пользователя.

        Raises:
            InvalidTokenError: Токен недействителен, истёк либо имеет
                другой служебный тип.
        """
        return await self._decode_typed_token(token=token, expected_type=REFRESH_TOKEN_TYPE)

    async def create_password_reset_token(self, user_id: int, expires_minutes: int) -> str:
        """Создать одноразовый токен для сброса пароля.

        Args:
            user_id: Идентификатор пользователя.
            expires_minutes: Время жизни токена в минутах.

        Returns:
            str: Закодированный токен сброса пароля.
        """
        return await self._create_typed_token(
            user_id=user_id,
            token_type=PASSWORD_RESET_TOKEN_TYPE,
            expires_delta=timedelta(minutes=expires_minutes),
        )

    async def decode_password_reset_token(self, token: str) -> int:
        """Расшифровать токен сброса пароля и вернуть идентификатор пользователя.

        Args:
            token: Закодированный токен сброса пароля.

        Returns:
            int: Идентификатор пользователя.

        Raises:
            InvalidTokenError: Токен недействителен, истёк либо имеет
                другой служебный тип.
        """
        return await self._decode_typed_token(
            token=token,
            expected_type=PASSWORD_RESET_TOKEN_TYPE,
        )

    async def get_token_ttl_seconds(self, token: str, expected_type: str | None = None) -> int:
        """Вернуть оставшееся время жизни токена в секундах.

        Просроченный токен читается намеренно: значение TTL нужно, чтобы
        корректно заполнить заголовок ``Retry-After`` и ротацию refresh-токена.

        Args:
            token: Закодированный токен.
            expected_type: Ожидаемый служебный тип, если его надо проверить.

        Returns:
            int: Оставшийся TTL, не меньше нуля.

        Raises:
            InvalidTokenError: Тип токена не совпадает с ожидаемым.
        """
        payload = await self._decode_payload(token, verify_exp=False)
        if expected_type and payload.get("token_type") != expected_type:
            raise InvalidTokenError(INVALID_TOKEN_TYPE_MESSAGE)
        exp = payload.get("exp")
        if exp is None:
            return 0
        remaining = int(float(exp) - datetime.now(UTC).timestamp())
        return max(remaining, 0)

    async def _create_typed_token(
        self,
        user_id: int,
        token_type: str,
        expires_delta: timedelta,
    ) -> str:
        """Собрать и закодировать токен заданного служебного типа.

        Args:
            user_id: Идентификатор пользователя.
            token_type: Служебный тип токена.
            expires_delta: Относительный срок истечения.

        Returns:
            str: Закодированный токен.
        """
        expire = datetime.now(UTC) + expires_delta
        payload = {"user_id": user_id, "token_type": token_type, "exp": expire}
        return jwt.encode(payload, Settings.secret_key, algorithm=ALGORITHM)

    async def _decode_typed_token(self, token: str, expected_type: str) -> int:
        """Расшифровать токен и убедиться в его служебном типе.

        Args:
            token: Закодированный токен.
            expected_type: Ожидаемый служебный тип.

        Returns:
            int: Идентификатор пользователя из полезной нагрузки.

        Raises:
            InvalidTokenError: Токен недействителен, истёк либо имеет
                другой тип.
        """
        payload = await self._decode_payload(token)
        if payload.get("token_type") != expected_type:
            raise InvalidTokenError(INVALID_TOKEN_TYPE_MESSAGE)
        return payload["user_id"]

    async def _decode_payload(self, token: str, verify_exp: bool = True) -> dict:
        """Расшифровать полезную нагрузку токена.

        Args:
            token: Закодированный токен.
            verify_exp: Проверять ли срок истечения.

        Returns:
            dict: Полезная нагрузка токена.

        Raises:
            InvalidTokenError: Токен недействителен или истёк.
        """
        try:
            return jwt.decode(
                token,
                Settings.secret_key,
                algorithms=[ALGORITHM],
                options={"verify_exp": verify_exp},
            )
        except jwt.PyJWTError as error:
            raise InvalidTokenError(str(error)) from error
