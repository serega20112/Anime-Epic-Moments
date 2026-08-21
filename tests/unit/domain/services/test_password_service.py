from __future__ import annotations

from backend.application.interface.services.password_service import PasswordServiceInterface


class TestPasswordServiceInterface:
    def test_abstract_method_names(self):
        assert {"hash_password", "verify_password"} <= set(
            PasswordServiceInterface.__abstractmethods__
        )

    def test_cannot_be_instantiated(self):
        try:
            PasswordServiceInterface()  # type: ignore[abstract]
            raised = False
        except TypeError:
            raised = True
        assert raised is True
