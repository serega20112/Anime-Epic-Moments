from __future__ import annotations

from types import SimpleNamespace

from backend.infrastructure.security.csrf_service import CSRFService


class TestCSRFService:
    def test_generate_token_stores_state(self):
        service = CSRFService()
        state = SimpleNamespace()
        token = service.generate_token(state)
        assert token
        assert state.csrf_token["value"] == token
        assert "expires_at" in state.csrf_token

    def test_get_token_from_state(self):
        service = CSRFService()
        state = SimpleNamespace()
        token = service.generate_token(state)
        assert service.get_token_from_state(state) == token

    def test_get_token_absent(self):
        service = CSRFService()
        assert service.get_token_from_state(SimpleNamespace()) is None

    def test_validate_missing_token(self):
        service = CSRFService()
        assert service.validate_token(SimpleNamespace(), "abc") is False

    def test_validate_mismatch(self):
        service = CSRFService()
        state = SimpleNamespace()
        service.generate_token(state)
        assert service.validate_token(state, "wrong") is False

    def test_validate_success(self):
        service = CSRFService()
        state = SimpleNamespace()
        token = service.generate_token(state)
        assert service.validate_token(state, token) is True

    def test_validate_form_csrf_missing(self):
        service = CSRFService()
        state = SimpleNamespace()
        service.generate_token(state)
        assert service.validate_form_csrf(state, {}) is False

    def test_validate_form_csrf_success(self):
        service = CSRFService()
        state = SimpleNamespace()
        token = service.generate_token(state)
        assert service.validate_form_csrf(state, {"csrf_token": token}) is True

    def test_validate_header_invalid_format(self):
        service = CSRFService()
        state = SimpleNamespace()
        service.generate_token(state)
        assert service.validate_header_csrf(state, "Token abc") is False

    def test_validate_header_success(self):
        service = CSRFService()
        state = SimpleNamespace()
        token = service.generate_token(state)
        assert service.validate_header_csrf(state, f"Bearer {token}") is True

    def test_tokens_are_unique(self):
        service = CSRFService()
        state1 = SimpleNamespace()
        state2 = SimpleNamespace()
        assert service.generate_token(state1) != service.generate_token(state2)
