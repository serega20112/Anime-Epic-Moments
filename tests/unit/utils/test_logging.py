from __future__ import annotations

import logging

import pytest

from backend.utils import logging as logging_module


class _CaptureHandler(logging.Handler):
    def __init__(self) -> None:
        super().__init__()
        self.records: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(record)


@pytest.mark.unit
class TestRequestIdFilter:
    async def test_defaults_to_dash(self):
        filter_ = logging_module.RequestIdFilter()
        filter_.request_id = None
        filter_.user_id = None
        record = logging.LogRecord("test", logging.INFO, "module", 1, "message", None, None)

        assert filter_.filter(record) is True
        assert record.request_id == "-"
        assert record.user_id == "-"

    async def test_uses_set_context_values(self):
        filter_ = logging_module.RequestIdFilter()
        filter_.request_id = "req-123"
        filter_.user_id = "user-456"
        record = logging.LogRecord("test", logging.INFO, "module", 1, "message", None, None)

        assert filter_.filter(record) is True
        assert record.request_id == "req-123"
        assert record.user_id == "user-456"


@pytest.mark.unit
class TestSetupLogging:
    async def test_clears_handlers_and_configures_root(self):
        await logging_module.setup_logging(level=logging.DEBUG)

        root = logging.getLogger()
        assert root.level == logging.DEBUG
        assert len(root.handlers) == 1
        handler = root.handlers[0]
        assert any(isinstance(f, logging_module.RequestIdFilter) for f in handler.filters)
        from pythonjsonlogger.json import JsonFormatter

        assert isinstance(handler.formatter, JsonFormatter)
        root.handlers.clear()


@pytest.mark.unit
class TestAuditLogger:
    async def test_get_audit_logger_sets_propagate_false_once(self):
        logger = await logging_module.get_audit_logger()
        assert isinstance(logger, logging.Logger)
        assert logger.propagate is False
        assert len(logger.handlers) == 1

        again = await logging_module.get_audit_logger()
        assert again is logger
        assert len(again.handlers) == 1

    async def test_log_business_event_writes_payload(self):
        logger = await logging_module.get_audit_logger()
        captured = _CaptureHandler()
        logger.addHandler(captured)
        try:
            await logging_module.log_business_event(
                event="support_ticket_created",
                user_id=42,
                ip_address="127.0.0.1",
                details={"ticket_id": "T-1"},
            )
        finally:
            logger.removeHandler(captured)

        assert len(captured.records) == 1
        record = captured.records[0]
        assert record.levelname == "INFO"
        payload = record.business_event
        assert payload["event"] == "support_ticket_created"
        assert payload["user_id"] == "42"
        assert payload["ip_address"] == "127.0.0.1"
        assert payload["ticket_id"] == "T-1"

    async def test_log_business_event_omits_missing_optional_fields(self):
        logger = await logging_module.get_audit_logger()
        captured = _CaptureHandler()
        logger.addHandler(captured)
        try:
            await logging_module.log_business_event(event="simple_event")
        finally:
            logger.removeHandler(captured)

        payload = captured.records[0].business_event
        assert payload == {"event": "simple_event"}

    async def test_log_security_event_writes_all_fields(self):
        logger = await logging_module.get_audit_logger()
        captured = _CaptureHandler()
        logger.addHandler(captured)
        try:
            await logging_module.log_security_event(
                event="login_failed",
                user_id="7",
                email="u@example.com",
                ip_address="10.0.0.1",
                details={"attempts": 3},
            )
        finally:
            logger.removeHandler(captured)

        payload = captured.records[0].security_event
        assert payload["event"] == "login_failed"
        assert payload["user_id"] == "7"
        assert payload["email"] == "u@example.com"
        assert payload["ip_address"] == "10.0.0.1"
        assert payload["attempts"] == 3

    async def test_log_security_event_omits_empty_optional_fields(self):
        logger = await logging_module.get_audit_logger()
        captured = _CaptureHandler()
        logger.addHandler(captured)
        try:
            await logging_module.log_security_event(event="account_locked")
        finally:
            logger.removeHandler(captured)

        payload = captured.records[0].security_event
        assert payload == {"event": "account_locked"}


@pytest.mark.unit
async def test_utils_facade_re_exports_logging_helpers():
    from backend import utils

    assert utils.setup_logging is logging_module.setup_logging
    assert utils.log_business_event is logging_module.log_business_event
    assert utils.log_security_event is logging_module.log_security_event
