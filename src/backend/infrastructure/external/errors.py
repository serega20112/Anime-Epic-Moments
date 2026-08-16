from __future__ import annotations

from backend.domain.exceptions import ExternalServiceError as DomainExternalServiceError


class ExternalServiceError(RuntimeError, DomainExternalServiceError):
    """Raised when a call to an external service fails.

    Inherits from RuntimeError so existing callers that treat delivery
    failures as non-fatal keep working unchanged, and from the domain-level
    :class:`backend.domain.exceptions.ExternalServiceError` so application
    layer code can catch it without depending on infrastructure.
    """

    service_name = "external"

    def __init__(self, message: str = "", *, service_name: str | None = None):
        super().__init__(message)
        self.service_name = service_name or self.service_name
        self.message = str(message)


class ExternalServiceTimeoutError(ExternalServiceError):
    """Raised when an external request exceeds its timeout."""

    service_name = "external"


class ExternalServiceUnavailableError(ExternalServiceError):
    """Raised when an external service is unreachable or rejects a request."""

    service_name = "external"


class ExternalServiceInvalidResponseError(ExternalServiceError):
    """Raised when an external service returns a malformed payload."""

    service_name = "external"


class ExternalServiceConfigurationError(ExternalServiceError):
    """Raised when an external service is not configured."""

    service_name = "external"
