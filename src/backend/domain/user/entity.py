import re
from datetime import datetime

from .exceptions import InvalidEmailError, InvalidUsernameError


class User:
    """Агрегат пользователя"""

    def __init__(
        self,
        email: str,
        username: str,
        password_hash: str,
        avatar_url: str | None = None,
        created_at: datetime | None = None,
        id: int | None = None,
    ):
        self._validate_email(email)
        self._validate_username(username)

        self.id: int | None = id
        self.email = email
        self.username = username
        self.avatar_url = avatar_url
        self.created_at = created_at or datetime.utcnow()
        self.password_hash = password_hash

    @staticmethod
    def _validate_email(email: str):
        pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
        if not re.match(pattern, email):
            raise InvalidEmailError(f"Неверный формат email: {email}")

    @staticmethod
    def _validate_username(username: str):
        if not (3 <= len(username) <= 20):
            raise InvalidUsernameError(
                f"Username должен быть от 3 до 20 символов, сейчас {len(username)}"
            )

    async def check_password(self, password: str) -> bool:
        raise NotImplementedError(
            "Password verification must be performed in application layer via PasswordService"
        )

    async def update_avatar(self, avatar_url: str):
        self.avatar_url = avatar_url

    async def change_username(self, new_username: str):
        self._validate_username(new_username)
        self.username = new_username
