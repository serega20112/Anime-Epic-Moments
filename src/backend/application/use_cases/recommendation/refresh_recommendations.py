"""Обновление рекомендаций пользователя."""

from __future__ import annotations

from backend.application.dto import RecommendationsQuery
from backend.application.interface.services import (
    RecommendationServiceInterface,
)
from backend.application.interface.unit_of_work import UnitOfWorkInterface
from backend.domain import RecommendationResult


class RefreshRecommendationsUseCase:
    """Генерирует новые рекомендации, игнорируя кэш."""

    def __init__(
        self,
        unit_of_work: UnitOfWorkInterface,
        service: RecommendationServiceInterface,
    ) -> None:
        """Инициализирует сценарий обновления рекомендаций.

        Args:
            unit_of_work: Граница транзакции чтения данных вкуса.
            service: Сервис рекомендаций.
        """
        self._unit_of_work = unit_of_work
        self._service = service

    async def execute(self, query: RecommendationsQuery) -> list[RecommendationResult]:
        """Генерирует новые рекомендации, игнорируя кэш.

        Args:
            query: Идентификатор пользователя и размер выборки.

        Returns:
            list[RecommendationResult]: Новый список рекомендаций.
        """
        async with self._unit_of_work as uow:
            return await self._service.generate(uow, query.user_id, query.limit, force_refresh=True)
