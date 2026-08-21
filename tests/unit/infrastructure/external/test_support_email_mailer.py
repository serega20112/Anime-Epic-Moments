from __future__ import annotations

from datetime import datetime
from email.message import EmailMessage

import pytest

from backend.config import Settings
from backend.domain.entities.support.support_ticket import SupportTicket
from backend.infrastructure.external.support_email_mailer import SupportEmailMailer


def _ticket(**overrides):
    payload = dict(
        id=5,
        user_id=3,
        email="user@example.com",
        username="tester",
        subject="  Big   subject  ",
        message="Hello there",
        channel="telegram",
        page_url="https://example.com/x",
        created_at=datetime(2025, 1, 2, 3, 4, 5),
    )
    payload.update(overrides)
    return SupportTicket(**payload)


class TestSupportEmailMailer:
    async def test_is_enabled_when_configured(self):
        assert await SupportEmailMailer().is_enabled() is True

    async def test_is_disabled_without_hosts(self, monkeypatch):
        monkeypatch.setattr(Settings, "smtp_host", "")
        monkeypatch.setattr(Settings, "support_email_to", [])
        assert await SupportEmailMailer().is_enabled() is False

    async def test_build_subject_truncates(self):
        mailer = SupportEmailMailer()
        subject = await mailer._build_subject(_ticket(subject="x" * 300))
        assert subject == f"AEM support #5: {'x' * 120}"

    async def test_build_subject_collapses_whitespace(self):
        mailer = SupportEmailMailer()
        subject = await mailer._build_subject(_ticket(subject="a   b"))
        assert subject == "AEM support #5: a b"

    async def test_build_plain_text_includes_fields(self):
        mailer = SupportEmailMailer()
        text = await mailer._build_plain_text(_ticket())
        assert "ID: 5" in text
        assert "Email: user@example.com" in text
        assert "User ID: 3" in text
        assert "Страница: https://example.com/x" in text
        assert "Hello there" in text
        assert "Создан: 2025-01-02 03:04:05 UTC" in text

    async def test_build_plain_text_guest_user(self):
        mailer = SupportEmailMailer()
        text = await mailer._build_plain_text(_ticket(user_id=None, page_url=None))
        assert "User ID: guest" in text
        assert "Страница" not in text

    async def test_send_returns_recipient_count(self, monkeypatch):
        class _FakeSMTP:
            def __init__(self, *args, **kwargs):
                pass

            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

            def starttls(self):
                pass

            def login(self, user, password):
                pass

            def send_message(self, message):
                assert isinstance(message, EmailMessage)
                assert message["Reply-To"] == "user@example.com"

        import smtplib

        recipient_count = len(Settings.support_email_to)
        monkeypatch.setattr(smtplib, "SMTP", _FakeSMTP)
        assert await SupportEmailMailer().send_ticket_created(_ticket()) == recipient_count

    async def test_send_raises_when_disabled(self, monkeypatch):
        monkeypatch.setattr(Settings, "smtp_host", "")
        with pytest.raises(RuntimeError):
            await SupportEmailMailer().send_ticket_created(_ticket())
