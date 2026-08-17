"""Structured JSON logging and security audit configuration."""

from __future__ import annotations

import logging
import sys
from contextvars import ContextVar
from typing import Any

from pythonjsonlogger.json import JsonFormatter

request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)
user_id_var: ContextVar[str | None] = ContextVar("user_id", default=None)


class RequestIdFilter(logging.Filter):
    """Attach request ID and user ID to log records.

    Reads the values from context variables set by the request logging
    middleware, falling back to the instance attributes for tests.
    """

    def __init__(self) -> None:
        super().__init__()
        self.request_id: str | None = None
        self.user_id: str | None = None

    def filter(self, record: logging.LogRecord) -> bool:
        """Add request and user context to the log record.

        Args:
            record: Log record being processed.

        Returns:
            bool: Always True to keep the record.
        """
        record.request_id = request_id_var.get() or self.request_id or "-"
        record.user_id = user_id_var.get() or self.user_id or "-"
        return True


async def _build_formatter() -> JsonFormatter:
    """Create a JSON formatter for structured logging.

    Returns:
        JsonFormatter: Configured JSON formatter.
    """
    return JsonFormatter(
        "%(asctime)s %(levelname)s %(name)s %(request_id)s %(user_id)s %(message)s",
        rename_fields={
            "asctime": "timestamp",
            "levelname": "level",
            "name": "logger",
        },
    )


async def setup_logging(*, level: int = logging.INFO) -> None:
    """Configure root logger with structured JSON output.

    Args:
        level: Logging level for the root logger.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(await _build_formatter())
    handler.addFilter(RequestIdFilter())

    root_logger.handlers.clear()
    root_logger.addHandler(handler)


async def get_audit_logger() -> logging.Logger:
    """Return the dedicated security audit logger.

    Returns:
        logging.Logger: Logger named 'security.audit'.
    """
    logger = logging.getLogger("security.audit")
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(await _build_formatter())
        logger.addHandler(handler)
        logger.propagate = False
    return logger


async def log_business_event(
    *,
    event: str,
    user_id: str | int | None = None,
    ip_address: str | None = None,
    details: dict[str, Any] | None = None,
) -> None:
    """Record a business audit event.

    Args:
        event: Business event name (e.g. support_ticket_created).
        user_id: User identifier if available.
        ip_address: Client IP address if available.
        details: Additional structured context.
    """
    audit_logger = await get_audit_logger()
    payload: dict[str, Any] = {"event": event}
    if user_id is not None:
        payload["user_id"] = str(user_id)
    if ip_address:
        payload["ip_address"] = ip_address
    if details:
        payload.update(details)
    audit_logger.info("business_event", extra={"business_event": payload})


async def log_security_event(
    *,
    event: str,
    user_id: str | None = None,
    email: str | None = None,
    ip_address: str | None = None,
    details: dict[str, Any] | None = None,
) -> None:
    """Record a security audit event.

    Args:
        event: Security event name (e.g. login_failed, account_locked).
        user_id: User identifier if available.
        email: User email if available.
        ip_address: Client IP address if available.
        details: Additional structured context.
    """
    audit_logger = await get_audit_logger()
    payload: dict[str, Any] = {"event": event}
    if user_id:
        payload["user_id"] = user_id
    if email:
        payload["email"] = email
    if ip_address:
        payload["ip_address"] = ip_address
    if details:
        payload.update(details)
    audit_logger.info("security_event", extra={"security_event": payload})
