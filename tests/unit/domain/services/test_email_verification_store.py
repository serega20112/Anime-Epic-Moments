from __future__ import annotations

from backend.domain.services.email_verification_store import EmailVerificationStoreInterface


class TestEmailVerificationStoreInterface:
    def test_abstract_method_names(self):
        assert {"generate_code", "verify_code", "has_pending"} <= set(
            EmailVerificationStoreInterface.__abstractmethods__
        )

    def test_cannot_be_instantiated(self):
        try:
            EmailVerificationStoreInterface()  # type: ignore[abstract]
            raised = False
        except TypeError:
            raised = True
        assert raised is True