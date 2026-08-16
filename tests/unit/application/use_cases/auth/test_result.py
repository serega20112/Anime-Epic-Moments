from __future__ import annotations

from backend.application.use_cases.auth.result import AuthResult


class TestAuthResult:
    def test_success_defaults(self):
        result = AuthResult.success(data=7)
        assert result.ok is True
        assert result.data == 7
        assert result.message is None
        assert result.redirect_endpoint is None
        assert result.redirect_email is None

    def test_success_fields(self):
        result = AuthResult.success(
            data="payload",
            message="done",
            redirect_endpoint="home",
            redirect_email="a@b.com",
        )
        assert result.message == "done"
        assert result.redirect_endpoint == "home"
        assert result.redirect_email == "a@b.com"

    def test_failure(self):
        result = AuthResult.failure("boom", "auth.login", "a@b.com")
        assert result.ok is False
        assert result.error_message == "boom"
        assert result.error_endpoint == "auth.login"
        assert result.redirect_email == "a@b.com"
        assert result.data is None
