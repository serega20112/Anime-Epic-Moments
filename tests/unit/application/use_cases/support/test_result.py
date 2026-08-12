from __future__ import annotations

from backend.application.use_cases.support.result import CreateSupportTicketResult


class TestCreateSupportTicketResult:
    def test_success(self):
        result = CreateSupportTicketResult.success(data="ticket", message="ok")
        assert result.ok is True
        assert result.status_code == 200
        assert result.data == "ticket"
        assert result.message == "ok"
        assert result.service_unavailable is False
        assert result.error_message is None

    def test_success_unavailable(self):
        result = CreateSupportTicketResult.success(
            data="ticket", service_unavailable=True
        )
        assert result.service_unavailable is True

    def test_failure(self):
        result = CreateSupportTicketResult.failure("nope", status_code=500)
        assert result.ok is False
        assert result.error_message == "nope"
        assert result.status_code == 500