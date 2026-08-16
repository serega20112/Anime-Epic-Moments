from __future__ import annotations

from backend.domain.services.jwt_service import JWTServiceInterface


class TestJWTServiceInterface:
    def test_abstract_method_names(self):
        assert {
            "create_access_token",
            "create_refresh_token",
            "decode_token",
            "decode_refresh_token",
            "create_password_reset_token",
            "decode_password_reset_token",
            "get_token_ttl_seconds",
        } <= set(JWTServiceInterface.__abstractmethods__)

    def test_cannot_be_instantiated(self):
        try:
            JWTServiceInterface()  # type: ignore[abstract]
            raised = False
        except TypeError:
            raised = True
        assert raised is True
