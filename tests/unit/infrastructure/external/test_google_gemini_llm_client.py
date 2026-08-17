from __future__ import annotations

import pytest

from backend.infrastructure.external.google_gemini_llm_client import GoogleGeminiLLMClient


async def test_gemini_client_returns_titles_from_completion(monkeypatch):
    """Проверяем, что Gemini-клиент берет названия из generateContent ответа."""
    client = GoogleGeminiLLMClient(api_key="key", model="gemini-2.0-flash")

    async def _fake_create_completion(model_route, messages):
        return {
            "candidates": [
                {
                    "content": {
                        "parts": [{"text": "Gintama"}, {"text": "KonoSuba"}, {"text": "Saiki"}]
                    }
                }
            ]
        }

    monkeypatch.setattr(client, "_create_completion", _fake_create_completion)

    queries, mode, error = await client.build_search_queries_with_meta(
        description="best comedy anime"
    )

    assert queries == ["Gintama", "KonoSuba", "Saiki"]
    assert mode == "gemini_llm_text"
    assert error is None


async def test_gemini_client_translates_messages_into_gemini_format():
    """Проверяем трансляцию OpenAI-style messages в генерацию запроса generateContent."""
    client = GoogleGeminiLLMClient(api_key="key", model="gemini-2.0-flash")
    requests_calls: list[tuple] = []

    class _FakeSession:
        trust_env = False

        def __init__(self, calls: list):
            self.calls = calls

        async def post(self, url, json, timeout):
            self.calls.append((url, json))
            response = _FakeResponse()
            return response

    class _FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"candidates": [{"content": {"parts": [{"text": "One Piece"}]}}]}

    client.session = _FakeSession(requests_calls)
    payload = await client._create_completion_with_timeout(
        model_route="gemini-2.0-flash",
        messages=[
            {"role": "system", "content": "Ты помощник"},
            {"role": "user", "content": "description: samurai\nage_rating: all"},
        ],
        timeout_seconds=30,
    )

    url, body = requests_calls[0]
    assert "models/gemini-2.0-flash:generateContent" in url
    assert "key=key" in url
    assert body["systemInstruction"] == {"parts": [{"text": "Ты помощник"}]}
    assert body["contents"] == [
        {"role": "user", "parts": [{"text": "description: samurai\nage_rating: all"}]}
    ]
    assert payload["candidates"][0]["content"]["parts"][0]["text"] == "One Piece"


async def test_gemini_client_resolves_plain_and_prefixed_models():
    """Проверяем, что Gemini model route не получает provider-суффикс."""
    plain = GoogleGeminiLLMClient(api_key="key", model="gemini-2.0-flash")
    prefixed = GoogleGeminiLLMClient(api_key="key", model="models/gemini-2.0-flash")

    assert await plain._resolve_model_route() == "gemini-2.0-flash"
    assert await prefixed._resolve_model_route() == "gemini-2.0-flash"


@pytest.mark.parametrize(
    "completion",
    [
        {},
        {"candidates": []},
        {"candidates": [{"content": None}]},
        {"candidates": [{"content": {"parts": []}}]},
    ],
)
async def test_gemini_client_extract_returns_empty_on_malformed(completion):
    """Проверяем, что поврежденные ответы Gemini не вызывают исключений."""
    client = GoogleGeminiLLMClient(api_key="key", model="gemini-2.0-flash")
    assert await client._extract_message_content(completion) == ""
