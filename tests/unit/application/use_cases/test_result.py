from __future__ import annotations

import dataclasses
import inspect

import pytest
from starlette import status

from backend.application.use_cases import UseCaseResult
from backend.application.use_cases.result import UseCaseResult as ExportedResult


@pytest.mark.unit
class TestUseCaseResult:
    """Юнит-тесты единого результата сценариев прикладного слоя."""

    def test_exported_from_use_case_facade(self):
        """Что тестируем: единый результат доступен из фасада сценариев.
        Что передаём: класс из модуля и из пакета use_cases.
        Что ожидаем: это один и тот же класс, а не копия на каждый домен.
        """
        assert ExportedResult is UseCaseResult

    def test_success_carries_data_and_ok_status(self):
        """Что тестируем: сборку успешного результата по умолчанию.
        Что передаём: только данные.
        Что ожидаем: ok=True, HTTP 200, данные на месте, ошибки нет.
        """
        result = UseCaseResult.success(data={"sources_count": 2})

        assert result.ok is True
        assert result.status_code == status.HTTP_200_OK
        assert result.data == {"sources_count": 2}
        assert result.error is None

    def test_success_honours_explicit_status_code(self):
        """Что тестируем: явный HTTP-код успешного ответа.
        Что передаём: данные и код 201.
        Что ожидаем: результат несёт переданный код.
        """
        result = UseCaseResult.success(data="x", status_code=status.HTTP_201_CREATED)

        assert result.status_code == status.HTTP_201_CREATED

    def test_failure_keeps_error_code_without_data(self):
        """Что тестируем: сборку результата с ошибкой.
        Что передаём: код ошибки и HTTP 422.
        Что ожидаем: ok=False, переданный статус, данные отсутствуют.
        """
        result = UseCaseResult.failure(
            "bad_input", status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
        )

        assert result.ok is False
        assert result.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert result.error == "bad_input"
        assert result.data is None

    def test_failure_defaults_to_bad_request(self):
        """Что тестируем: статус ошибки по умолчанию.
        Что передаём: только код ошибки.
        Что ожидаем: HTTP 400.
        """
        result = UseCaseResult.failure("provider_not_configured")

        assert result.status_code == status.HTTP_400_BAD_REQUEST

    def test_factories_are_synchronous(self):
        """Что тестируем: конструкторы результата — синхронные classmethod'ы.
        Что передаём: методы success и failure единого результата.
        Что ожидаем: ни один не является корутиной, вызов даёт значение сразу.
        """
        assert not inspect.iscoroutinefunction(UseCaseResult.success)
        assert not inspect.iscoroutinefunction(UseCaseResult.failure)
        assert isinstance(UseCaseResult.success(), UseCaseResult)

    def test_result_is_frozen_value(self):
        """Что тестируем: неизменяемость результата как значения.
        Что передаём: попытку перезаписать поле созданного результата.
        Что ожидаем: FrozenInstanceError — сценарий не «доделывает» итог после возврата.
        """
        result = UseCaseResult.success(data="x")

        with pytest.raises(dataclasses.FrozenInstanceError):
            result.data = "y"
