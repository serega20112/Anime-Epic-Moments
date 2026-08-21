from __future__ import annotations

from datetime import datetime

import pytest

from backend.config import Settings
from backend.domain.entities.support.support_ticket import SupportTicket
from backend.infrastructure.external.telegram_support_notifier import TelegramSupportNotifier


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


class TestTelegramSupportNotifier:
    async def test_is_enabled(self):
        assert await TelegramSupportNotifier().is_enabled() is True

    async def test_is_disabled_without_bot(self, monkeypatch):
        monkeypatch.setattr(Settings, "telegram_support_bot_token", "")
        monkeypatch.setattr(Settings, "telegram_support_admin_chat_ids", [])
        assert await TelegramSupportNotifier().is_enabled() is False

    def test_truncate_short(self):
        notifier = TelegramSupportNotifier()
        assert notifier._truncate(" abc ", 10) == "abc"

    def test_truncate_long(self):
        notifier = TelegramSupportNotifier()
        result = notifier._truncate("x" * 20, 5)
        assert len(result) == 5
        assert result.endswith("…")

    def test_build_message_escapes_html(self):
        notifier = TelegramSupportNotifier()
        message = notifier._build_message(_ticket(username="<b>evil</b>"))
        assert "<b>evil</b>" not in message
        assert "&lt;b&gt;evil&lt;/b&gt;" in message

    def test_build_message_includes_id_and_subject(self):
        notifier = TelegramSupportNotifier()
        message = notifier._build_message(_ticket())
        assert "<b>ID:</b> 5" in message
        assert "<b>Тема:</b> Big" in message
        assert "subject" in message
        assert "<b>Страница:</b> https://example.com/x" in message

    def test_build_message_guest_and_no_page(self):
        notifier = TelegramSupportNotifier()
        message = notifier._build_message(_ticket(id=None, user_id=None, page_url=None))
        assert "<b>ID:</b> new" in message
        assert "<b>User ID:</b> guest" in message
        assert "<b>Страница:</b>" not in message

    async def test_send_delivers_to_all_chats(self, monkeypatch):
        notifier = TelegramSupportNotifier()
        made = []

        class _Response:
            def raise_for_status(self):
                pass

            def json(self):
                return {"ok": True}

        class _Session:
            async def post(self, *args, **kwargs):
                made.append(kwargs.get("json", {}).get("chat_id"))
                return _Response()

        monkeypatch.setattr(notifier, "session", _Session())
        result = await notifier.send_ticket_created(_ticket())
        assert result == len(Settings.telegram_support_admin_chat_ids)
        assert len(made) == len(Settings.telegram_support_admin_chat_ids)

    async def test_send_raises_when_all_chats_fail(self, monkeypatch):
        notifier = TelegramSupportNotifier()

        class _Response:
            def raise_for_status(self):
                raise RuntimeError("boom")

        class _Session:
            async def post(self, *args, **kwargs):
                return _Response()

        monkeypatch.setattr(notifier, "session", _Session())
        with pytest.raises(RuntimeError):
            await notifier.send_ticket_created(_ticket())

    async def test_send_raises_when_not_configured(self, monkeypatch):
        monkeypatch.setattr(Settings, "telegram_support_bot_token", "")
        notifier = TelegramSupportNotifier()
        monkeypatch.setattr(notifier, "admin_chat_ids", [])
        with pytest.raises(RuntimeError):
            await notifier.send_ticket_created(_ticket())
