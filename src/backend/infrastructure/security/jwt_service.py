from datetime import UTC, datetime, timedelta

import jwt

from backend.config import Settings

ALGORITHM = "HS256"


class JWTService:
    """Создание и проверка JWT токенов"""

    async def create_token(self, user_id: int) -> str:
        return await self.create_access_token(user_id)

    async def create_access_token(self, user_id: int) -> str:
        return await self._create_typed_token(
            user_id=user_id,
            token_type="access",
            expires_delta=timedelta(minutes=Settings.access_token_expire_minutes),
        )

    async def create_refresh_token(self, user_id: int) -> str:
        return await self._create_typed_token(
            user_id=user_id,
            token_type="refresh",
            expires_delta=timedelta(days=Settings.refresh_token_expire_days),
        )

    async def decode_token(self, token: str) -> int:
        """Возвращает user_id если токен валиден, иначе кидает исключение"""
        return await self._decode_typed_token(token=token, expected_type="access")

    async def decode_refresh_token(self, token: str) -> int:
        """Возвращает user_id из refresh token."""
        return await self._decode_typed_token(token=token, expected_type="refresh")

    async def create_password_reset_token(self, user_id: int, expires_minutes: int) -> str:
        """Создает токен для сброса пароля."""
        return await self._create_typed_token(
            user_id=user_id,
            token_type="password_reset",
            expires_delta=timedelta(minutes=expires_minutes),
        )

    async def decode_password_reset_token(self, token: str) -> int:
        """Возвращает user_id из токена сброса пароля."""
        return await self._decode_typed_token(token=token, expected_type="password_reset")

    async def get_token_ttl_seconds(self, token: str, expected_type: str | None = None) -> int:
        """Возвращает оставшийся TTL токена в секундах."""
        payload = await self._decode_payload(token, verify_exp=False)
        if expected_type and payload.get("token_type") != expected_type:
            raise jwt.InvalidTokenError("Invalid token type")
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
        expire = datetime.now(UTC) + expires_delta
        payload = {"user_id": user_id, "token_type": token_type, "exp": expire}
        return jwt.encode(payload, Settings.secret_key, algorithm=ALGORITHM)

    async def _decode_typed_token(self, token: str, expected_type: str) -> int:
        payload = await self._decode_payload(token)
        if payload.get("token_type") != expected_type:
            raise jwt.InvalidTokenError("Invalid token type")
        return payload["user_id"]

    async def _decode_payload(self, token: str, verify_exp: bool = True) -> dict:
        return jwt.decode(
            token,
            Settings.secret_key,
            algorithms=[ALGORITHM],
            options={"verify_exp": verify_exp},
        )
