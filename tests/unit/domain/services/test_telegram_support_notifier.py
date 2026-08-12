from __future__ import annotations

from backend.domain.services.telegram_support_notifier import TelegramSupportNotifierInterface


class TestTelegramSupportNotifierInterface:
    def test_abstract_method_names(self):
        assert "notify" in set(TelegramSupportNotifierInterface.__abstractmethods__)

    def test_cannot_be_instantiated(self):
        try:
            TelegramSupportNotifierInterface()  # type: ignore[abstract]
            raised = False
        except TypeError:
            raised = True
        assert raised is True