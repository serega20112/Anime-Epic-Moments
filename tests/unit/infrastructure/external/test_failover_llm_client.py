from __future__ import annotations

import pytest

from backend.infrastructure.external.failover_llm_client import FailoverLLMClient
from backend.infrastructure.external.huggingface_llm_client import HuggingFaceLLMClient


class _StubClient:
    """Client stub with configurable outcomes and recorded calls."""

    def __init__(self, *, api_key: str | None = "key", mode: str = "ok_mode", taste_result=None):
        self.api_key = api_key
        self.mode = mode
        self.query_calls: list[str] = []
        self.taste_calls: list[str] = []
        self.taste_result = taste_result

    async def describe_taste_profile(self, profile_data: dict, fallback: str) -> str:
        self.taste_calls.append(str(profile_data))
        if self.taste_result is not None:
            return self.taste_result
        return f"{self.mode}-taste"

    async def build_search_queries_with_meta(self, description: str, **kwargs):
        self.query_calls.append(description)
        if self.mode.startswith("fallback"):
            return ["fallback-query"], self.mode, "boom"
        return ["title-a", "title-b"], self.mode, None


@pytest.mark.unit
class TestFailoverLLMClient:
    async def test_uses_primary_when_it_succeeds(self):
        primary = _StubClient(api_key="key", mode="gemini_llm_text")
        fallback = _StubClient(api_key="hf", mode="hf_llm_text")
        client = FailoverLLMClient(primary=primary, fallback=fallback)

        queries, mode, error = await client.build_search_queries_with_meta(
            description="samurai comedy", genre_hint="comedy"
        )

        assert queries == ["title-a", "title-b"]
        assert mode == "gemini_llm_text"
        assert error is None
        assert primary.query_calls == ["samurai comedy"]
        assert fallback.query_calls == []

    async def test_falls_back_to_secondary_when_primary_fails(self):
        primary = _StubClient(api_key="key", mode="fallback_exception")
        fallback = _StubClient(api_key="hf", mode="hf_llm_text")
        client = FailoverLLMClient(primary=primary, fallback=fallback)

        queries, mode, error = await client.build_search_queries_with_meta(
            description="school comedy", genre_hint="comedy"
        )

        assert queries == ["title-a", "title-b"]
        assert mode == "hf_llm_text"
        assert primary.query_calls == ["school comedy"]
        assert fallback.query_calls == ["school comedy"]

    async def test_skips_primary_when_it_is_not_configured(self):
        primary = _StubClient(api_key=None, mode="gemini_llm_text")
        fallback = _StubClient(api_key="hf", mode="hf_llm_text")
        client = FailoverLLMClient(primary=primary, fallback=fallback)

        queries, mode, _error = await client.build_search_queries_with_meta(description="isekai")

        assert mode == "hf_llm_text"
        assert primary.query_calls == []
        assert fallback.query_calls == ["isekai"]

    async def test_returns_secondary_fallback_when_both_fail(self):
        primary = _StubClient(api_key="key", mode="fallback_exception")
        fallback = _StubClient(api_key="hf", mode="fallback_invalid_json")
        client = FailoverLLMClient(primary=primary, fallback=fallback)

        queries, mode, error = await client.build_search_queries_with_meta(description="mecha")

        assert queries == ["fallback-query"]
        assert mode == "fallback_invalid_json"
        assert error == "boom"

    async def test_taste_profile_used_from_primary_when_successful(self):
        primary = _StubClient(api_key="key", mode="gemini_llm_text")
        fallback = _StubClient(api_key="hf", mode="hf_llm_text")
        client = FailoverLLMClient(primary=primary, fallback=fallback)

        result = await client.describe_taste_profile({"mood": "x"}, fallback="fb")

        assert result == "gemini_llm_text-taste"
        assert primary.taste_calls == ["{'mood': 'x'}"]
        assert fallback.taste_calls == []

    async def test_taste_profile_falls_back_when_primary_returns_fallback_text(self):
        primary = _StubClient(api_key="key", mode="gemini_llm_text", taste_result="fb")
        fallback = _StubClient(api_key="hf", mode="hf_llm_text")
        client = FailoverLLMClient(primary=primary, fallback=fallback)

        result = await client.describe_taste_profile({"mood": "x"}, fallback="fb")

        assert result == "hf_llm_text-taste"
        assert fallback.taste_calls == ["{'mood': 'x'}"]

    async def test_works_with_real_huggingface_client(self, monkeypatch):
        """Проверяем интеграцию failover с настоящим HF-клиентом."""
        hf = HuggingFaceLLMClient(api_key="hf-token", model="openai/gpt-oss-120b", provider="x")

        async def _fake_create_completion(model_route, messages):
            return {"choices": [{"message": {"content": "Gintama\nKonoSuba\nSaiki"}}]}

        monkeypatch.setattr(hf, "_create_completion", _fake_create_completion)
        client = FailoverLLMClient(primary=_StubClient(api_key=None), fallback=hf)

        queries, mode, error = await client.build_search_queries_with_meta(description="comedy")

        assert queries == ["Gintama", "KonoSuba", "Saiki"]
        assert mode == "hf_llm_text"
        assert error is None
