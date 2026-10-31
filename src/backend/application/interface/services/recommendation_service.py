"""Порт сервиса рекомендаций."""

from __future__ import annotations

from abc import ABC, abstractmethod

from backend.application.interface.unit_of_work import UnitOfWorkInterface
from backend.domain.value_objects.recommendation.recommendation_result import (
    RecommendationResult,
)


class RecommendationServiceInterface(ABC):
    """Подбор рекомендаций аниме по вкусу пользователя.

    Границу транзакции передаёт вызывающий сценарий: сервис читает избранное и
    хайлайты через репозитории единицы работы и не заводит собственных.
    """

    @abstractmethod
    async def generate(
        self,
        unit_of_work: UnitOfWorkInterface,
        user_id: int,
        limit: int = 5,
        force_refresh: bool = False,
    ) -> list[RecommendationResult]:
        """Подобрать рекомендации для пользователя.

        Args:
            unit_of_work: Граница транзакции чтения данных вкуса.
            user_id: Идентификатор пользователя.
            limit: Максимальное число рекомендаций.
            force_refresh: Признак сброса кэша и пересчёта подборки.

        Returns:
            list[RecommendationResult]: Рекомендации в порядке убывания похожести.
        """

    @abstractmethod
    async def invalidate_user(self, user_id: int) -> None:
        """Сбросить кэш рекомендаций пользователя.

        Args:
            user_id: Идентификатор пользователя.
        """
