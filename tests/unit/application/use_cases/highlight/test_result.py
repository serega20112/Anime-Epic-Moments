from __future__ import annotations

from backend.application.use_cases.highlight.result import HighlightResult


class TestHighlightResult:
    def test_success_defaults(self):
        result = HighlightResult.success(data="x")
        assert result.ok is True
        assert result.status_code == 200
        assert result.data == "x"
        assert result.error is None

    def test_success_status(self):
        result = HighlightResult.success(data="x", status_code=201)
        assert result.status_code == 201

    def test_failure(self):
        result = HighlightResult.failure("bad", status_code=422)
        assert result.ok is False
        assert result.error == "bad"
        assert result.status_code == 422
        assert result.data is None