"""Base domain exception hierarchy for the application."""

from __future__ import annotations


class DomainError(Exception):
    """Base exception for all domain-level errors."""


class NotFoundError(DomainError):
    """Raised when a requested resource does not exist."""


class ValidationError(DomainError):
    """Raised when input data fails validation."""


class AuthenticationError(DomainError):
    """Raised when authentication fails."""


class AuthorizationError(DomainError):
    """Raised when the user lacks permission."""


class DuplicateError(DomainError):
    """Raised when attempting to create a duplicate resource."""


class ExternalServiceError(DomainError):
    """Raised when an external API or service call fails."""