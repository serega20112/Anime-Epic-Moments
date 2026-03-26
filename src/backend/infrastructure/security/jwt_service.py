import jwt
from datetime import datetime, timedelta
from src.backend.dependencies.settings import Settings

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1 день


class JWTService:
    """
    Создание и проверка JWT токенов
    """

    def create_token(self, user_id: int) -> str:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        payload = {"user_id": user_id, "token_type": "access", "exp": expire}
        token = jwt.encode(payload, Settings.secret_key, algorithm=ALGORITHM)
        return token

    def decode_token(self, token: str) -> int:
        """
        Возвращает user_id если токен валиден, иначе кидает исключение
        """
        payload = jwt.decode(token, Settings.secret_key, algorithms=[ALGORITHM])
        if payload.get("token_type") != "access":
            raise jwt.InvalidTokenError("Invalid token type")
        return payload["user_id"]

    def create_password_reset_token(self, user_id: int, expires_minutes: int) -> str:
        """Создает токен для сброса пароля."""
        expire = datetime.utcnow() + timedelta(minutes=expires_minutes)
        payload = {"user_id": user_id, "token_type": "password_reset", "exp": expire}
        return jwt.encode(payload, Settings.secret_key, algorithm=ALGORITHM)

    def decode_password_reset_token(self, token: str) -> int:
        """Возвращает user_id из токена сброса пароля."""
        payload = jwt.decode(token, Settings.secret_key, algorithms=[ALGORITHM])
        if payload.get("token_type") != "password_reset":
            raise jwt.InvalidTokenError("Invalid token type")
        return payload["user_id"]
