from __future__ import annotations

from backend.domain.exceptions import (
    AuthenticationError,
    AuthorizationError,
    DomainError,
    DuplicateError,
    ExternalServiceError,
    NotFoundError,
    ValidationError,
)


class TestDomainExceptions:
    def test_all_are_domain_errors(self):
        for exc_type in (
            NotFoundError,
            ValidationError,
            AuthenticationError,
            AuthorizationError,
            DuplicateError,
            ExternalServiceError,
        ):
            assert issubclass(exc_type, DomainError)

    def test_instances_are_raiseable(self):
        error = NotFoundError("missing")
        assert isinstance(error, DomainError)
        assert str(error) == "missing"

    def test_validation_error(self):
        assert isinstance(ValidationError("bad"), ValidationError)

    def test_external_service_error(self):
        assert isinstance(ExternalServiceError("timeout"), ExternalServiceError)
