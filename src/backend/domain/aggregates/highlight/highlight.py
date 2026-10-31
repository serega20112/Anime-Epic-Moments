"""Агрегат хайлайта: момента, отмеченного пользователем в серии."""

from datetime import datetime

from backend.domain.clock import utc_now
from backend.domain.exceptions import AuthorizationError, ValidationError


class Highlight:
    """Доменный агрегат, описывающий пользовательский хайлайт.

    Агрегат владеет правилами целостности момента: корректностью номера серии,
    порядка временных меток и правом владения, без которого изменение и
    удаление хайлайта недопустимы.
    """

    def __init__(
        self,
        user_id: int | None,
        anime_id: int,
        episode: int,
        start_timestamp: float,
        end_timestamp: float,
        title: str = "",
        category: str | None = None,
        description: str = "",
        is_spoiler: bool = False,
        emotion: str | None = None,
        created_at: datetime | None = None,
    ):
        """Создаёт новый хайлайт.

        Args:
            user_id: Идентификатор автора или None для гостя.
            anime_id: Идентификатор аниме.
            episode: Номер серии, нумерация с единицы.
            start_timestamp: Начало момента в секундах.
            end_timestamp: Конец момента в секундах.
            title: Название хайлайта.
            category: Необязательная категория.
            description: Описание хайлайта.
            is_spoiler: Содержит ли хайлайт спойлер.
            emotion: Необязательная метка эмоции.
            created_at: Время создания, по умолчанию текущее UTC.

        Raises:
            ValidationError: Некорректный номер серии или неверный порядок меток.
        """
        self.id: int | None = None
        self.user_id = user_id
        self.anime_id = anime_id
        self.episode = episode
        self.start_timestamp = start_timestamp
        self.end_timestamp = end_timestamp
        self.title = str(title or "").strip()
        self.category = self._normalize_optional_text(category)
        self.description = description
        self.is_spoiler = is_spoiler
        self.emotion = self._normalize_optional_text(emotion)
        self.likes_count = 0
        self.views_count = 0
        self.created_at = created_at or utc_now()

        self._validate()

    def _validate(self) -> None:
        """Проверяет инварианты хайлайта.

        Raises:
            ValidationError: Номер серии меньше единицы или метки расположены
                в неправильном порядке.
        """
        if self.episode < 1:
            raise ValidationError(f"Номер серии должен быть не меньше 1, получено {self.episode}")
        if self.start_timestamp >= self.end_timestamp:
            raise ValidationError(
                f"start_timestamp ({self.start_timestamp}) должен быть меньше "
                f"end_timestamp ({self.end_timestamp})"
            )

    def is_owned_by(self, user_id: int | None) -> bool:
        """Проверяет, принадлежит ли хайлайт указанному пользователю.

        Args:
            user_id: Идентификатор проверяемого пользователя.

        Returns:
            bool: True, если хайлайт принадлежит пользователю.
        """
        return user_id is not None and self.user_id == user_id

    def ensure_editable_by(self, user_id: int | None) -> None:
        """Проверяет право редактирования и удаления хайлайта.

        Args:
            user_id: Идентификатор пользователя, выполняющего операцию.

        Raises:
            AuthorizationError: Хайлайт принадлежит другому пользователю либо
                является гостевым.
        """
        if not self.is_owned_by(user_id):
            raise AuthorizationError("Изменять хайлайт может только его автор")

    def edit(
        self,
        start_timestamp: float,
        end_timestamp: float,
        title: str,
        category: str | None,
        description: str,
        is_spoiler: bool,
        emotion: str | None = None,
        episode: int | None = None,
    ) -> None:
        """Обновляет содержимое хайлайта.

        Args:
            start_timestamp: Новое начало момента в секундах.
            end_timestamp: Новый конец момента в секундах.
            title: Новое название.
            category: Новая категория.
            description: Новое описание.
            is_spoiler: Содержит ли хайлайт спойлер.
            emotion: Новая метка эмоции.
            episode: Новый номер серии, None оставляет прежний.

        Raises:
            ValidationError: Нарушен инвариант номера серии или меток времени.
        """
        self.start_timestamp = start_timestamp
        self.end_timestamp = end_timestamp
        self.title = str(title or "").strip()
        self.category = self._normalize_optional_text(category)
        self.description = description
        self.is_spoiler = is_spoiler
        self.emotion = self._normalize_optional_text(emotion)
        if episode is not None:
            self.episode = int(episode)
        self._validate()

    def add_like(self) -> None:
        """Увеличивает счётчик лайков на единицу."""
        self.likes_count += 1

    def add_view(self) -> None:
        """Увеличивает счётчик просмотров на единицу."""
        self.views_count += 1

    @staticmethod
    def _normalize_optional_text(value: str | None) -> str | None:
        """Нормализует необязательный текст или возвращает None.

        Args:
            value: Исходное значение.

        Returns:
            str | None: Нормализованный текст либо None для пустого значения.
        """
        text = str(value or "").strip()
        return text or None
