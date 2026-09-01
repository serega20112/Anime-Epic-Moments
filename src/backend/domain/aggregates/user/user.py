import re
from datetime import datetime

from backend.domain.aggregates.user.exceptions import InvalidEmailError, InvalidUsernameError
from backend.domain.policies.user_credentials_policy import (
    EMAIL_PATTERN,
    USERNAME_MAX_LENGTH,
    USERNAME_MIN_LENGTH,
)

STATUS_MAX_LENGTH = 80


class User:
    """Агрегат пользователя"""

    def __init__(
        self,
        email: str,
        username: str,
        password_hash: str,
        avatar_url: str | None = None,
        status: str | None = None,
        show_watch_activity: bool = True,
        show_recent_episodes: bool = True,
        created_at: datetime | None = None,
        id: int | None = None,
    ):
        self._validate_email(email)
        self._validate_username(username)

        self.id: int | None = id
        self.email = email
        self.username = username
        self.avatar_url = avatar_url
        self.status = self._clean_status(status)
        self.show_watch_activity = bool(show_watch_activity)
        self.show_recent_episodes = bool(show_recent_episodes)
        self.created_at = created_at or datetime.utcnow()
        self.password_hash = password_hash

    @staticmethod
    def _clean_status(status: str | None) -> str | None:
        if status is None:
            return None
        cleaned = str(status).strip()
        if not cleaned:
            return None
        if len(cleaned) > STATUS_MAX_LENGTH:
            raise ValueError(f"Статус не может быть длиннее {STATUS_MAX_LENGTH} символов")
        return cleaned

    @staticmethod
    def _validate_email(email: str):
        if not re.match(EMAIL_PATTERN, email):
            raise InvalidEmailError(f"Неверный формат email: {email}")

    @staticmethod
    def _validate_username(username: str):
        if not (USERNAME_MIN_LENGTH <= len(username) <= USERNAME_MAX_LENGTH):
            raise InvalidUsernameError(
                f"Username должен быть от {USERNAME_MIN_LENGTH} до {USERNAME_MAX_LENGTH} символов, "
                f"сейчас {len(username)}"
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

    def change_status(self, status: str | None):
        self.status = self._clean_status(status)

    def toggle_watch_activity_visibility(self, visible: bool):
        self.show_watch_activity = bool(visible)

    def toggle_recent_episodes_visibility(self, visible: bool):
        self.show_recent_episodes = bool(visible)
