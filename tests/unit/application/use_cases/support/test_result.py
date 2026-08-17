from __future__ import annotations

from backend.application.use_cases.support.result import CreateSupportTicketResult


class TestCreateSupportTicketResult:
    async def test_success(self):
        result = await CreateSupportTicketResult.success(data="ticket", message="ok")
        assert result.ok is True
        assert result.status_code == 200
        assert result.data == "ticket"
        assert result.message == "ok"
        assert result.service_unavailable is False
        assert result.error_message is None

    async def test_success_unavailable(self):
        result = await CreateSupportTicketResult.success(data="ticket", service_unavailable=True)
        assert result.service_unavailable is True

    async def test_failure(self):
        result = await CreateSupportTicketResult.failure("nope", status_code=500)
        assert result.ok is False
        assert result.error_message == "nope"
        assert result.status_code == 500
