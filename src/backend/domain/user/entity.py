import re
from datetime import datetime
from typing import Optional
from .exceptions import *


class User:
    """
    Агрегат пользователя
    """

    def __init__(
        self,
        email: str,
        username: str,
        password_hash: str,
        avatar_url: Optional[str] = None,
        created_at: Optional[datetime] = None,
        id: Optional[int] = None,
    ):
        self._validate_email(email)
        self._validate_username(username)

        self.id: Optional[int] = id
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

    def check_password(self, password: str) -> bool:
        raise NotImplementedError(
            "Password verification must be performed in application layer via PasswordService"
        )

    def update_avatar(self, avatar_url: str):
        self.avatar_url = avatar_url

    def change_username(self, new_username: str):
        self._validate_username(new_username)
        self.username = new_username
