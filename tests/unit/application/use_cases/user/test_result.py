from __future__ import annotations

from backend.application.use_cases.user.result import UserResult


class TestUserResult:
    def test_success(self):
        result = UserResult.success(data="u")
        assert result.ok is True
        assert result.data == "u"
        assert result.status_code == 200
        assert result.error is None

    def test_failure(self):
        result = UserResult.failure("conflict", status_code=409)
        assert result.ok is False
        assert result.error == "conflict"
        assert result.status_code == 409