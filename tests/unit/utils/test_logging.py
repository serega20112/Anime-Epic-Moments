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


def _record(message: str = "message") -> logging.LogRecord:
    return logging.LogRecord("test", logging.INFO, "module", 1, message, None, None)


@pytest.mark.unit
class TestRequestIdFilter:
    def test_defaults_to_dash(self):
        filter_ = logging_module.RequestIdFilter()
        filter_.request_id = None
        filter_.user_id = None
        record = _record()

        assert filter_.filter(record) is True
        assert record.request_id == "-"
        assert record.user_id == "-"

    def test_uses_set_context_values(self):
        filter_ = logging_module.RequestIdFilter()
        filter_.request_id = "req-123"
        filter_.user_id = "user-456"
        record = _record()

        assert filter_.filter(record) is True
        assert record.request_id == "req-123"
        assert record.user_id == "user-456"


@pytest.mark.unit
class TestMaskSecrets:
    def test_masks_query_token_and_key(self):
        text = "GET https://kodik-api.com/search?token=abc123&title=Gintama"

        assert logging_module.mask_secrets(text) == (
            "GET https://kodik-api.com/search?token=***&title=Gintama"
        )

    def test_masks_authorization_credential(self):
        text = "Authorization: Bearer eyJhbGciOiJIUzI1NiJ9.payload.signature"

        assert logging_module.mask_secrets(text) == "Authorization: Bearer ***"

    def test_masks_email_domain(self):
        text = "login failed for user@example.com"

        assert logging_module.mask_secrets(text) == "login failed for ***@example.com"

    def test_keeps_plain_text_untouched(self):
        text = "request_finished method=GET path=/watch/19 status=200"

        assert logging_module.mask_secrets(text) == text

    def test_secret_mask_filter_rewrites_record_message(self):
        filter_ = logging_module.SecretMaskFilter()
        record = logging.LogRecord(
            "httpx",
            logging.INFO,
            "module",
            1,
            "HTTP Request: GET https://kodik-api.com/search?token=%s",
            ("abc123",),
            None,
        )

        assert filter_.filter(record) is True
        assert record.msg == "HTTP Request: GET https://kodik-api.com/search?token=***"
        assert record.args is None


@pytest.mark.unit
class TestBuildFormatter:
    def test_json_formatter_renames_fields(self):
        record = _record("schema_verified")
        record.request_id = "-"
        record.user_id = "-"

        output = logging_module.build_formatter("json").format(record)

        assert '"timestamp": "20' in output
        assert '"level": "INFO"' in output
        assert '"logger": "test"' in output
        assert '"message": "schema_verified"' in output

    def test_text_formatter_is_readable(self):
        record = _record("application_started")
        record.request_id = "req-1"
        record.user_id = "42"

        output = logging_module.build_formatter("text").format(record)

        assert "INFO" in output
        assert "req-1" in output
        assert "application_started" in output
        assert output.count("20") >= 1

    def test_unknown_format_falls_back_to_text(self):
        assert isinstance(logging_module.build_formatter("yaml"), logging.Formatter)


@pytest.mark.unit
class TestSetupLogging:
    def test_clears_handlers_and_configures_root(self):
        logging_module.setup_logging(level=logging.DEBUG)

        root = logging.getLogger()
        assert root.level == logging.DEBUG
        assert len(root.handlers) == 1
        handler = root.handlers[0]
        assert any(isinstance(f, logging_module.RequestIdFilter) for f in handler.filters)
        assert any(isinstance(f, logging_module.SecretMaskFilter) for f in handler.filters)
        from pythonjsonlogger.json import JsonFormatter

        assert isinstance(handler.formatter, JsonFormatter)
        root.handlers.clear()

    def test_quiets_noisy_third_party_loggers(self):
        logging_module.setup_logging(fmt="text")

        assert logging.getLogger("httpx").level == logging.WARNING
        assert logging.getLogger("uvicorn.access").disabled is True
        logging.getLogger("uvicorn.access").disabled = False


@pytest.mark.unit
class TestAuditLogger:
    def test_get_audit_logger_sets_propagate_false_once(self):
        logger = logging_module.get_audit_logger()
        assert isinstance(logger, logging.Logger)
        assert logger.propagate is False
        assert self._own_handlers(logger) == 1

        again = logging_module.get_audit_logger()
        assert again is logger
        assert self._own_handlers(again) == 1

    @staticmethod
    def _own_handlers(logger: logging.Logger) -> int:
        """Посчитать обработчики, добавленные самим логгером аудита.

        Плагин логирования pytest во время прогона навешивает свои перехватчики
        на чужие логгеры, поэтому считается только собственный поток вывода журнала.

        Args:
            logger: Логгер событий безопасности.

        Returns:
            int: Число собственных обработчиков вывода.
        """
        return len(
            [handler for handler in logger.handlers if type(handler) is logging.StreamHandler]
        )

    def test_log_business_event_writes_payload(self):
        logger = logging_module.get_audit_logger()
        captured = _CaptureHandler()
        logger.addHandler(captured)
        try:
            logging_module.log_business_event(
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

    def test_log_business_event_omits_missing_optional_fields(self):
        logger = logging_module.get_audit_logger()
        captured = _CaptureHandler()
        logger.addHandler(captured)
        try:
            logging_module.log_business_event(event="simple_event")
        finally:
            logger.removeHandler(captured)

        payload = captured.records[0].business_event
        assert payload == {"event": "simple_event"}

    def test_log_security_event_writes_all_fields(self):
        logger = logging_module.get_audit_logger()
        captured = _CaptureHandler()
        logger.addHandler(captured)
        try:
            logging_module.log_security_event(
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

    def test_log_security_event_omits_empty_optional_fields(self):
        logger = logging_module.get_audit_logger()
        captured = _CaptureHandler()
        logger.addHandler(captured)
        try:
            logging_module.log_security_event(event="account_locked")
        finally:
            logger.removeHandler(captured)

        payload = captured.records[0].security_event
        assert payload == {"event": "account_locked"}


@pytest.mark.unit
def test_utils_facade_re_exports_logging_helpers():
    from backend import utils

    assert utils.setup_logging is logging_module.setup_logging
    assert utils.log_business_event is logging_module.log_business_event
    assert utils.log_security_event is logging_module.log_security_event
