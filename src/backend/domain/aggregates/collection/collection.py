"""Агрегат пользовательской коллекции аниме."""

from __future__ import annotations

from datetime import UTC, datetime

from backend.domain.exceptions import AuthorizationError, ValidationError

TITLE_MAX_LENGTH = 80
DESCRIPTION_MAX_LENGTH = 400


class AnimeCollection:
    """Агрегат пользовательской коллекции аниме.

    Хранит правила целостности коллекции и право владения: менять состав
    коллекции может только её владелец.
    """

    def __init__(
        self,
        user_id: int,
        title: str,
        description: str = "",
        is_public: bool = True,
        cover_url: str | None = None,
        created_at: datetime | None = None,
        id: int | None = None,
    ):
        """Создать коллекцию.

        Args:
            user_id: Идентификатор владельца.
            title: Название коллекции.
            description: Описание коллекции.
            is_public: Видна ли коллекция другим пользователям.
            cover_url: Ссылка на обложку.
            created_at: Время создания, по умолчанию текущее UTC.
            id: Идентификатор, присваивается хранилищем.

        Raises:
            ValidationError: Пустое или слишком длинное название либо слишком
                длинное описание.
        """
        self.id = id
        self.user_id = int(user_id)
        self.title = str(title or "").strip()
        self.description = str(description or "").strip()
        self.is_public = bool(is_public)
        self.cover_url = str(cover_url).strip() if cover_url else None
        self.created_at = created_at or datetime.now(UTC)
        self._validate()

    def _validate(self) -> None:
        """Проверить инварианты коллекции.

        Raises:
            ValidationError: Название или описание выходит за границы.
        """
        if not self.title or len(self.title) > TITLE_MAX_LENGTH:
            raise ValidationError("Название коллекции должно быть от 1 до 80 символов")
        if len(self.description) > DESCRIPTION_MAX_LENGTH:
            raise ValidationError("Описание коллекции не должно превышать 400 символов")

    def is_owned_by(self, user_id: int | None) -> bool:
        """Проверить принадлежность коллекции пользователю.

        Args:
            user_id: Идентификатор проверяемого пользователя.

        Returns:
            bool: True, если коллекция принадлежит пользователю.
        """
        return user_id is not None and self.user_id == int(user_id)

    def ensure_owned_by(self, user_id: int | None) -> None:
        """Проверить право изменения коллекции.

        Args:
            user_id: Идентификатор пользователя, выполняющего операцию.

        Raises:
            AuthorizationError: Коллекция принадлежит другому пользователю.
        """
        if not self.is_owned_by(user_id):
            raise AuthorizationError("Нет доступа к этой коллекции")
