"""Агрегат пользователя: учётные данные, профиль и видимость активности."""

import re
from datetime import datetime

from backend.domain.aggregates.user.exceptions import InvalidEmailError, InvalidUsernameError
from backend.domain.clock import utc_now
from backend.domain.exceptions import ValidationError
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
        google_subject: str | None = None,
        email_verified: bool = False,
    ):
        """Создать пользователя с заданными учётными данными и профилем."""
        self._validate_email(email)
        self._validate_username(username)

        self.id: int | None = id
        self.email = email
        self.username = username
        self.avatar_url = avatar_url
        self.status = self._clean_status(status)
        self.show_watch_activity = bool(show_watch_activity)
        self.show_recent_episodes = bool(show_recent_episodes)
        self.created_at = created_at or utc_now()
        self.password_hash = password_hash
        self.google_subject = google_subject
        self.email_verified = bool(email_verified)

    @staticmethod
    def _clean_status(status: str | None) -> str | None:
        """Привести статус профиля к допустимому виду.

        Args:
            status: Введённый пользователем статус либо None.

        Returns:
            str | None: Текст статуса без обрамляющих пробелов либо None для пустого ввода.

        Raises:
            ValidationError: Если статус длиннее допустимого предела.
        """
        if status is None:
            return None
        cleaned = str(status).strip()
        if not cleaned:
            return None
        if len(cleaned) > STATUS_MAX_LENGTH:
            raise ValidationError(f"Статус не может быть длиннее {STATUS_MAX_LENGTH} символов")
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

    def update_avatar(self, avatar_url: str):
        """Обновить адрес аватара пользователя."""
        self.avatar_url = avatar_url

    def change_username(self, new_username: str):
        """Сменить имя пользователя с проверкой длины."""
        self._validate_username(new_username)
        self.username = new_username

    def change_status(self, status: str | None):
        """Сменить статус профиля с проверкой длины."""
        self.status = self._clean_status(status)

    def toggle_watch_activity_visibility(self, visible: bool):
        """Переключить видимость истории просмотра."""
        self.show_watch_activity = bool(visible)

    def toggle_recent_episodes_visibility(self, visible: bool):
        """Переключить видимость недавних серий."""
        self.show_recent_episodes = bool(visible)

    def link_google(self, google_subject: str) -> None:
        """Привязать аккаунт к Google и отметить почту подтверждённой.

        Args:
            google_subject: Стабильный идентификатор аккаунта Google.
        """
        self.google_subject = google_subject
        self.email_verified = True

    def unlink_google(self) -> None:
        """Отвязать аккаунт от Google."""
        self.google_subject = None
