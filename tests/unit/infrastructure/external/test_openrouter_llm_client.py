from __future__ import annotations

from backend.infrastructure.external.openrouter_llm_client import (
    DEFAULT_OPENROUTER_API_URL,
    OpenRouterLLMClient,
)


async def test_openrouter_llm_client_uses_fallback_without_api_key():
    """Без API-ключа клиент уходит в fallback-режим, как HF."""
    client = OpenRouterLLMClient(api_key=None, model="stealth/ox-alpha")

    queries, mode, error = await client.build_search_queries_with_meta(
        description="funny samurai anime",
        genre_hint="comedy",
    )

    assert queries == ["funny samurai anime comedy"]
    assert mode == "fallback_no_token"
    assert error is None


async def test_openrouter_llm_client_passes_model_route_as_is():
    """Модель vendor/model передаётся без HF-суффикса провайдера."""
    client = OpenRouterLLMClient(api_key="token", model="stealth/ox-alpha")

    assert await client._resolve_model_route() == "stealth/ox-alpha"
    assert client.api_url == DEFAULT_OPENROUTER_API_URL


async def test_openrouter_llm_client_parses_completion(monkeypatch):
    """Валидный completion парсится в список тайтлов с режимом openrouter."""
    client = OpenRouterLLMClient(api_key="token", model="stealth/ox-alpha")

    async def _fake_create_completion(model_route, messages):
        return {"choices": [{"message": {"content": "Gintama\nKonoSuba"}}]}

    monkeypatch.setattr(client, "_create_completion", _fake_create_completion)

    queries, mode, error = await client.build_search_queries_with_meta(
        description="best comedy anime"
    )

    assert queries == ["Gintama", "KonoSuba"]
    assert mode == "openrouter_llm_text"
    assert error is None


async def test_openrouter_llm_client_falls_back_on_error(monkeypatch):
    """Сбой запроса даёт fallback-запрос и режим exception."""
    client = OpenRouterLLMClient(api_key="token", model="stealth/ox-alpha")

    async def _fake_create_completion(model_route, messages):
        raise RuntimeError("boom")

    monkeypatch.setattr(client, "_create_completion", _fake_create_completion)

    queries, mode, error = await client.build_search_queries_with_meta(description="school comedy")

    assert queries == ["school comedy"]
    assert mode == "fallback_exception"
