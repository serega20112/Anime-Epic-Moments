from __future__ import annotations

import inspect

from backend.application.interface.services.recommendation_service import (
    RecommendationServiceInterface,
)
from backend.application.services.recommendation_service import RecommendationService


class TestRecommendationServiceInterface:
    """Тесты контракта порта сервиса рекомендаций."""

    def test_abstract_method_names(self):
        """Что тестируем: порт описывает методы, которые вызывают сценарии.
        Что передаём: набор абстрактных методов порта.
        Что ожидаем: генерация с переданной границей транзакции и сброс кэша.
        """
        assert {"generate", "invalidate_user"} == set(
            RecommendationServiceInterface.__abstractmethods__
        )

    def test_cannot_be_instantiated(self):
        """Что тестируем: порт нельзя создать напрямую.
        Что передаём: попытку инстанцировать абстрактный класс.
        Что ожидаем: TypeError.
        """
        try:
            RecommendationServiceInterface()  # type: ignore[abstract]
            raised = False
        except TypeError:
            raised = True
        assert raised is True

    def test_implementation_covers_every_port_method(self):
        """Что тестируем: реализация закрывает порт без пропущенных методов.
        Что передаём: каждый абстрактный метод порта.
        Что ожидаем: у сервиса есть метод с тем же набором параметров.
        """
        for method_name in RecommendationServiceInterface.__abstractmethods__:
            port_method = getattr(RecommendationServiceInterface, method_name)
            implementation = getattr(RecommendationService, method_name, None)
            assert implementation is not None, method_name
            assert list(inspect.signature(port_method).parameters) == list(
                inspect.signature(implementation).parameters
            )

    def test_service_does_not_own_a_repository(self):
        """Что тестируем: сервис не держит собственные репозитории.
        Что передаём: сигнатуру конструктора сервиса.
        Что ожидаем: репозиториев среди параметров нет — чтение идёт через uow.
        """
        parameters = list(inspect.signature(RecommendationService.__init__).parameters)

        assert "fav_repo" not in parameters
        assert "highlight_repo" not in parameters
