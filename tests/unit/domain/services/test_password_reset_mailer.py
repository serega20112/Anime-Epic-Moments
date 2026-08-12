from __future__ import annotations

from backend.domain.services.password_reset_mailer import PasswordResetMailerInterface


class TestPasswordResetMailerInterface:
    def test_abstract_method_names(self):
        assert "send_reset_email" in set(PasswordResetMailerInterface.__abstractmethods__)

    def test_cannot_be_instantiated(self):
        try:
            PasswordResetMailerInterface()  # type: ignore[abstract]
            raised = False
        except TypeError:
            raised = True
        assert raised is True