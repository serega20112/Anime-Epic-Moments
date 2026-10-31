"""Общие кирпичики внешних интеграций: ошибки транспорта и защита ответа.

Подпакет не содержит предметной логики и не знает про конкретных провайдеров — только то,
что нужно всем клиентам одинаково:

- `errors` — семейство исключений `ExternalService*`, которые сценарии переводят в
  понятные отказы;
- `http_guard` — чтение JSON-ответа с лимитом размера, чтобы злонамеренно большой ответ
  не съел память процесса.

Клиенты провайдеров импортируют имена отсюда, а не из конкретных модулей: внутреннее
деление можно менять, не трогая потребителей.
"""

from __future__ import annotations

from .errors import (
    ExternalServiceConfigurationError,
    ExternalServiceError,
    ExternalServiceInvalidResponseError,
    ExternalServiceTimeoutError,
    ExternalServiceUnavailableError,
)
from .http_guard import read_json_limited

__all__ = [
    "ExternalServiceConfigurationError",
    "ExternalServiceError",
    "ExternalServiceInvalidResponseError",
    "ExternalServiceTimeoutError",
    "ExternalServiceUnavailableError",
    "read_json_limited",
]
