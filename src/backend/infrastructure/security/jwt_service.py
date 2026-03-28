import jwt
from datetime import datetime, timedelta, timezone
from src.backend.dependencies.settings import Settings

ALGORITHM = "HS256"


class JWTService:
    """
    Создание и проверка JWT токенов
    """

    def create_token(self, user_id: int) -> str:
        return self.create_access_token(user_id)

    def create_access_token(self, user_id: int) -> str:
        return self._create_typed_token(
            user_id=user_id,
            token_type="access",
            expires_delta=timedelta(minutes=Settings.access_token_expire_minutes),
        )

    def create_refresh_token(self, user_id: int) -> str:
        return self._create_typed_token(
            user_id=user_id,
            token_type="refresh",
            expires_delta=timedelta(days=Settings.refresh_token_expire_days),
        )

    def decode_token(self, token: str) -> int:
        """
        Возвращает user_id если токен валиден, иначе кидает исключение
        """
        return self._decode_typed_token(token=token, expected_type="access")

    def decode_refresh_token(self, token: str) -> int:
        """Возвращает user_id из refresh token."""
        return self._decode_typed_token(token=token, expected_type="refresh")

    def create_password_reset_token(self, user_id: int, expires_minutes: int) -> str:
        """Создает токен для сброса пароля."""
        return self._create_typed_token(
            user_id=user_id,
            token_type="password_reset",
            expires_delta=timedelta(minutes=expires_minutes),
        )

    def decode_password_reset_token(self, token: str) -> int:
        """Возвращает user_id из токена сброса пароля."""
        return self._decode_typed_token(token=token, expected_type="password_reset")

    def get_token_ttl_seconds(
        self, token: str, expected_type: str | None = None
    ) -> int:
        """Возвращает оставшийся TTL токена в секундах."""
        payload = self._decode_payload(token, verify_exp=False)
        if expected_type and payload.get("token_type") != expected_type:
            raise jwt.InvalidTokenError("Invalid token type")
        exp = payload.get("exp")
        if exp is None:
            return 0
        remaining = int(float(exp) - datetime.now(timezone.utc).timestamp())
        return max(remaining, 0)

    def _create_typed_token(
        self,
        user_id: int,
        token_type: str,
        expires_delta: timedelta,
    ) -> str:
        expire = datetime.now(timezone.utc) + expires_delta
        payload = {"user_id": user_id, "token_type": token_type, "exp": expire}
        return jwt.encode(payload, Settings.secret_key, algorithm=ALGORITHM)

    def _decode_typed_token(self, token: str, expected_type: str) -> int:
        payload = self._decode_payload(token)
        if payload.get("token_type") != expected_type:
            raise jwt.InvalidTokenError("Invalid token type")
        return payload["user_id"]

    def _decode_payload(self, token: str, verify_exp: bool = True) -> dict:
        return jwt.decode(
            token,
            Settings.secret_key,
            algorithms=[ALGORITHM],
            options={"verify_exp": verify_exp},
        )
