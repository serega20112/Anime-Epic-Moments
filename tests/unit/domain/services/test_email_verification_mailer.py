from __future__ import annotations

from backend.domain.services.email_verification_mailer import EmailVerificationMailerInterface


class TestEmailVerificationMailerInterface:
    def test_abstract_method_names(self):
        assert "send_verification_email" in set(
            EmailVerificationMailerInterface.__abstractmethods__
        )

    def test_cannot_be_instantiated(self):
        try:
            EmailVerificationMailerInterface()  # type: ignore[abstract]
            raised = False
        except TypeError:
            raised = True
        assert raised is True