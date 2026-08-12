from __future__ import annotations

import pytest

from backend.domain.support.entity import SupportTicket
from backend.infrastructure.repositories.support_repository import SupportRepository


@pytest.mark.integration
class TestSupportRepository:
    async def test_adds_and_reads_ticket(self, async_db_session):
        repo = SupportRepository(async_db_session)
        ticket = SupportTicket(
            email="a@b.com",
            username="tester",
            subject="Help",
            message="Broken page",
            channel="email",
            user_id=1,
            page_url="https://x.com",
        )

        saved = await repo.add(ticket)

        assert saved.id is not None
        assert saved.email == "a@b.com"
        assert saved.status == "open"
        assert saved.delivery_status == "pending"

    async def test_update_existing_ticket(self, async_db_session):
        repo = SupportRepository(async_db_session)
        ticket = SupportTicket(
            email="a@b.com",
            username="tester",
            subject="S",
            message="M",
            channel="telegram",
        )
        saved = await repo.add(ticket)

        saved.status = "resolved"
        saved.delivery_status = "sent"
        updated = await repo.update(saved)

        assert updated.id == saved.id
        assert updated.status == "resolved"
        assert updated.delivery_status == "sent"

    async def test_update_missing_ticket_raises(self, async_db_session):
        repo = SupportRepository(async_db_session)
        ticket = SupportTicket(
            id=999,
            email="a@b.com",
            username="t",
            subject="S",
            message="M",
        )
        with pytest.raises(ValueError):
            await repo.update(ticket)