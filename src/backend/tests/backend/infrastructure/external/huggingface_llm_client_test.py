from __future__ import annotations

import pytest

from src.backend.infrastructure.external.huggingface_llm_client import HuggingFaceLLMClient


def test_huggingface_llm_client_uses_fallback_without_api_key():
    """Проверяем, что HuggingFaceLLMClient переходит в fallback-режим без API key."""
    client = HuggingFaceLLMClient(api_key=None, model="model", provider="provider")

    queries, mode, error = client.build_search_queries_with_meta(
        description="funny samurai anime",
        genre_hint="comedy",
    )

    assert queries == ["funny samurai anime comedy"]
    assert mode == "fallback_no_token"
    assert error is None


@pytest.mark.parametrize(
    ("model", "provider", "expected"),
    [
        ("openai/gpt-oss-120b", "fireworks-ai", "openai/gpt-oss-120b:fireworks-ai"),
        ("repo:model-route", "ignored", "repo:model-route"),
        ("plain-model", None, "plain-model"),
    ],
)
def test_huggingface_llm_client_resolves_model_route(model, provider, expected):
    """Проверяем, что HuggingFaceLLMClient корректно формирует model route."""
    client = HuggingFaceLLMClient(api_key="token", model=model, provider=provider)

    assert client._resolve_model_route() == expected


def test_huggingface_llm_client_parses_up_to_three_title_candidates():
    """Проверяем, что HuggingFaceLLMClient извлекает только валидные title-кандидаты из ответа модели."""
    client = HuggingFaceLLMClient(api_key="token", model="model", provider="provider")

    parsed = client._parse_queries(
        "1. Gintama\nanime with daily life scenes\nKonoSuba\nSaiki Kusuo no Psi-nan\nFourth Title"
    )

    assert parsed == ["Gintama", "KonoSuba", "Saiki Kusuo no Psi-nan"]


def test_huggingface_llm_client_returns_model_titles_from_completion(monkeypatch):
    """Проверяем, что HuggingFaceLLMClient берет названия из completion и не уходит в fallback при валидном ответе."""
    client = HuggingFaceLLMClient(api_key="token", model="model", provider="provider")
    monkeypatch.setattr(
        client,
        "_create_completion",
        lambda model_route, messages: {
            "choices": [{"message": {"content": "Gintama\nKonoSuba\nSaiki Kusuo no Psi-nan"}}]
        },
    )

    queries, mode, error = client.build_search_queries_with_meta(description="best comedy anime")

    assert queries == ["Gintama", "KonoSuba", "Saiki Kusuo no Psi-nan"]
    assert mode == "hf_llm_text"
    assert error is None


def test_huggingface_llm_client_falls_back_when_completion_raises(monkeypatch):
    """Проверяем, что HuggingFaceLLMClient возвращает fallback-запрос и режим exception при сбое completion."""
    client = HuggingFaceLLMClient(api_key="token", model="model", provider="provider")
    monkeypatch.setattr(
        client,
        "_create_completion",
        lambda model_route, messages: (_ for _ in ()).throw(RuntimeError("boom")),
    )

    queries, mode, error = client.build_search_queries_with_meta(description="school comedy")

    assert queries == ["school comedy"]
    assert mode == "fallback_exception"
    assert "RuntimeError" in error
