from __future__ import annotations

import pytest

from backend.application.dto.support_commands import CreateSupportTicketCommand


class TestCreateSupportTicketCommand:
    def test_stores_fields(self):
        command = CreateSupportTicketCommand(
            user_id=4,
            email="a@b.com",
            username="t",
            subject="s",
            message="m",
            channel="telegram",
            page_url="https://example.com/x",
        )
        assert command.user_id == 4
        assert command.email == "a@b.com"
        assert command.username == "t"
        assert command.subject == "s"
        assert command.message == "m"
        assert command.channel == "telegram"
        assert command.page_url == "https://example.com/x"

    def test_page_url_defaults_to_none(self):
        command = CreateSupportTicketCommand(
            user_id=None,
            email="a@b.com",
            username="t",
            subject="s",
            message="m",
            channel="email",
        )
        assert command.page_url is None

    def test_is_frozen(self):
        command = CreateSupportTicketCommand(
            user_id=None,
            email="a@b.com",
            username="t",
            subject="s",
            message="m",
            channel="email",
        )
        with pytest.raises(Exception):
            command.channel = "telegram"
