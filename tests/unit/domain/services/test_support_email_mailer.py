from __future__ import annotations

from backend.domain.services.support_email_mailer import SupportEmailMailerInterface


class TestSupportEmailMailerInterface:
    def test_abstract_method_names(self):
        assert "send" in set(SupportEmailMailerInterface.__abstractmethods__)

    def test_cannot_be_instantiated(self):
        try:
            SupportEmailMailerInterface()  # type: ignore[abstract]
            raised = False
        except TypeError:
            raised = True
        assert raised is True
