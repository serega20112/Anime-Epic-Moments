from abc import ABC, abstractmethod

from backend.domain.moment.entity import ViewingMoment


class MomentRepository(ABC):
    @abstractmethod
    async def save_moment(self, moment: ViewingMoment) -> ViewingMoment:
        """Создает или обновляет черновой момент просмотра."""

    @abstractmethod
    async def get_moment(self, moment_id: int, user_id: int) -> ViewingMoment | None:
        """Возвращает момент просмотра, принадлежащий пользователю."""

    @abstractmethod
    async def get_moments_by_user(self, user_id: int) -> list[ViewingMoment]:
        """Возвращает черновые моменты пользователя."""

    @abstractmethod
    async def delete_moment(self, moment_id: int, user_id: int) -> bool:
        """Удаляет черновой момент просмотра пользователя."""
