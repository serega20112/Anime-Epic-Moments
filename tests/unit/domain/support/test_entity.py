from __future__ import annotations

from datetime import datetime

from backend.domain.entities.support.support_ticket import SupportTicket


class TestSupportTicket:
    async def test_stores_fields(self):
        ticket = SupportTicket(
            email="a@b.com",
            username="t",
            subject="s",
            message="m",
            channel="email",
            user_id=3,
            page_url="https://x.com",
            delivery_error="err",
        )
        assert ticket.id is None
        assert ticket.user_id == 3
        assert ticket.email == "a@b.com"
        assert ticket.username == "t"
        assert ticket.subject == "s"
        assert ticket.message == "m"
        assert ticket.channel == "email"
        assert ticket.page_url == "https://x.com"
        assert ticket.status == "open"
        assert ticket.delivery_status == "pending"
        assert ticket.delivery_error == "err"
        assert isinstance(ticket.created_at, datetime)

    async def test_defaults(self):
        ticket = SupportTicket(email="a@b.com", username="t", subject="s", message="m")
        assert ticket.channel == "telegram"
        assert ticket.user_id is None
        assert ticket.page_url is None
        assert ticket.delivery_status == "pending"
        assert ticket.delivery_error is None

    async def test_mark_delivered(self):
        ticket = SupportTicket(email="a@b.com", username="t", subject="s", message="m")
        ticket.delivery_error = "old"
        ticket.mark_delivered()
        assert ticket.delivery_status == "sent"
        assert ticket.delivery_error is None

    async def test_mark_delivery_failed(self):
        ticket = SupportTicket(email="a@b.com", username="t", subject="s", message="m")
        ticket.mark_delivery_failed("  connection refused  ")
        assert ticket.delivery_status == "failed"
        assert ticket.delivery_error == "connection refused"

    async def test_mark_delivery_failed_blank_becomes_unknown(self):
        ticket = SupportTicket(email="a@b.com", username="t", subject="s", message="m")
        ticket.mark_delivery_failed("   ")
        assert ticket.delivery_error == "unknown"

    async def test_mark_delivery_failed_truncates_long_error(self):
        ticket = SupportTicket(email="a@b.com", username="t", subject="s", message="m")
        ticket.mark_delivery_failed("x" * 1000)
        assert len(ticket.delivery_error) == 500
