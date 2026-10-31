"""Единица работы поверх сессии SQLAlchemy."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from backend.application.interface.repositories import (
    CollectionRepository as CollectionRepositoryPort,
)
from backend.application.interface.repositories import FavoriteRepository as FavoriteRepositoryPort
from backend.application.interface.repositories import (
    HighlightRepository as HighlightRepositoryPort,
)
from backend.application.interface.repositories import MomentRepository as MomentRepositoryPort
from backend.application.interface.repositories import RatingRepository as RatingRepositoryPort
from backend.application.interface.repositories import ReactionRepository as ReactionRepositoryPort
from backend.application.interface.repositories import SupportRepository as SupportRepositoryPort
from backend.application.interface.repositories import UserRepository as UserRepositoryPort
from backend.application.interface.repositories import WatchRepository as WatchRepositoryPort
from backend.application.interface.unit_of_work import UnitOfWorkInterface
from backend.infrastructure.database.repositories.collection_repository import CollectionRepository
from backend.infrastructure.database.repositories.favorite_repository import FavoriteRepository
from backend.infrastructure.database.repositories.highlight_repository import HighlightRepository
from backend.infrastructure.database.repositories.moment_repository import MomentRepository
from backend.infrastructure.database.repositories.rating_repository import RatingRepository
from backend.infrastructure.database.repositories.reaction_repository import ReactionRepository
from backend.infrastructure.database.repositories.support_repository import SupportRepository
from backend.infrastructure.database.repositories.user_repository import UserRepository
from backend.infrastructure.database.repositories.watch_repository import WatchRepository

_REPOSITORY_TYPES: dict[type, type] = {
    CollectionRepositoryPort: CollectionRepository,
    FavoriteRepositoryPort: FavoriteRepository,
    HighlightRepositoryPort: HighlightRepository,
    MomentRepositoryPort: MomentRepository,
    RatingRepositoryPort: RatingRepository,
    ReactionRepositoryPort: ReactionRepository,
    SupportRepositoryPort: SupportRepository,
    UserRepositoryPort: UserRepository,
    WatchRepositoryPort: WatchRepository,
}


class SqlAlchemyUnitOfWork(UnitOfWorkInterface):
    """Единица работы на общей асинхронной сессии базы.

    Репозитории складывают изменения в текущую транзакцию, а этот адаптер
    фиксирует её или откатывает. Экземпляры репозиториев создаются один раз
    на единицу работы и переиспользуются до её завершения.
    """

    def __init__(self, session: AsyncSession):
        """Создать единицу работы поверх сессии базы."""
        super().__init__()
        self._session = session
        self._repositories: dict[type, object] = {}

    def repository(self, repository_type):
        """Вернуть репозиторий порта, привязанный к текущей сессии.

        Args:
            repository_type: Порт репозитория из слоя application.

        Returns:
            Единственный на эту единицу работы экземпляр репозитория.

        Raises:
            LookupError: Если для порта не зарегистрирован адаптер.
        """
        existing = self._repositories.get(repository_type)
        if existing is not None:
            return existing
        try:
            implementation = _REPOSITORY_TYPES[repository_type]
        except KeyError as error:
            raise LookupError(
                f"Для порта {repository_type.__name__} нет адаптера репозитория"
            ) from error
        instance = implementation(self._session)
        self._repositories[repository_type] = instance
        return instance

    async def commit(self) -> None:
        """Зафиксировать все накопленные изменения атомарно.

        Raises:
            Exception: Если база отклонила транзакцию.
        """
        await self._session.commit()

    async def rollback(self) -> None:
        """Отменить все накопленные изменения."""
        await self._session.rollback()
