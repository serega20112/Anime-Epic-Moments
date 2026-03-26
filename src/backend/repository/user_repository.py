"""
Интерфейс репозитория для User агрегата.
Отделяет домен от конкретного хранилища (PostgreSQL / любой другой DB).
"""

from abc import ABC, abstractmethod
from typing import Optional
from src.backend.domain.user.entity import User


class UserRepository(ABC):
    @abstractmethod
    def add(self, user: User) -> User:
        """Сохраняет нового пользователя и возвращает с id"""

    @abstractmethod
    def get_by_email(self, email: str) -> Optional[User]:
        """Получает пользователя по email"""

    @abstractmethod
    def get_by_id(self, user_id: int) -> Optional[User]:
        """Получает пользователя по id"""

    @abstractmethod
    def update(self, user: User) -> User:
        """Обновляет существующего пользователя"""

    @abstractmethod
    def update_password(self, user_id: int, password_hash: str) -> User:
        """Обновляет пароль существующего пользователя"""
