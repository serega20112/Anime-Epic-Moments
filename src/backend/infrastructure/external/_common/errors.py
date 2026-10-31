"""Общие ошибки обращения к внешним сервисам."""

from __future__ import annotations

from backend.domain.exceptions import ExternalServiceError as DomainExternalServiceError


class ExternalServiceError(RuntimeError, DomainExternalServiceError):
    """Вызывается при неудачном обращении к внешнему сервису.

    Наследуется от RuntimeError, чтобы прежние вызовы, считающие сбой
    доставки некритичным, продолжали работать.
    """

    service_name = "external"

    def __init__(self, message: str = "", *, service_name: str | None = None):
        """Создать ошибку с именем внешнего сервиса."""
        super().__init__(message)
        self.service_name = service_name or self.service_name
        self.message = str(message)


class ExternalServiceTimeoutError(ExternalServiceError):
    """Внешний запрос превысил допустимое время ожидания."""

    service_name = "external"


class ExternalServiceUnavailableError(ExternalServiceError):
    """Внешний сервис недоступен или отклонил запрос."""

    service_name = "external"


class ExternalServiceInvalidResponseError(ExternalServiceError):
    """Внешний сервис вернул ответ неожиданного формата."""

    service_name = "external"


class ExternalServiceConfigurationError(ExternalServiceError):
    """Внешний сервис не настроен."""

    service_name = "external"
