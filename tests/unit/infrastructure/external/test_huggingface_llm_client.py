from __future__ import annotations

import pytest

from backend.infrastructure.external.huggingface_llm_client import HuggingFaceLLMClient


async def test_huggingface_llm_client_uses_fallback_without_api_key():
    """Проверяем, что HuggingFaceLLMClient переходит в fallback-режим без API key."""
    client = HuggingFaceLLMClient(api_key=None, model="model", provider="provider")

    queries, mode, error = await client.build_search_queries_with_meta(
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
async def test_huggingface_llm_client_resolves_model_route(model, provider, expected):
    """Проверяем, что HuggingFaceLLMClient корректно формирует model route."""
    client = HuggingFaceLLMClient(api_key="token", model=model, provider=provider)

    assert await client._resolve_model_route() == expected


async def test_huggingface_llm_client_parses_up_to_three_title_candidates():
    """Проверяем, что HuggingFaceLLMClient извлекает только валидные title-кандидаты из ответа модели."""
    client = HuggingFaceLLMClient(api_key="token", model="model", provider="provider")

    parsed = await client._parse_queries(
        "1. Gintama\nanime with daily life scenes\nKonoSuba\nSaiki Kusuo no Psi-nan\nFourth Title"
    )

    assert parsed == ["Gintama", "KonoSuba", "Saiki Kusuo no Psi-nan"]


async def test_huggingface_llm_client_returns_model_titles_from_completion(monkeypatch):
    """Проверяем, что HuggingFaceLLMClient берет названия из completion и не уходит в fallback при валидном ответе."""
    client = HuggingFaceLLMClient(api_key="token", model="model", provider="provider")

    async def _fake_create_completion(model_route, messages):
        return {
            "choices": [{"message": {"content": "Gintama\nKonoSuba\nSaiki Kusuo no Psi-nan"}}]
        }

    monkeypatch.setattr(client, "_create_completion", _fake_create_completion)

    queries, mode, error = await client.build_search_queries_with_meta(description="best comedy anime")

    assert queries == ["Gintama", "KonoSuba", "Saiki Kusuo no Psi-nan"]
    assert mode == "hf_llm_text"
    assert error is None


async def test_huggingface_llm_client_falls_back_when_completion_raises(monkeypatch):
    """Проверяем, что HuggingFaceLLMClient возвращает fallback-запрос и режим exception при сбое completion."""
    client = HuggingFaceLLMClient(api_key="token", model="model", provider="provider")

    async def _fake_create_completion(model_route, messages):
        raise RuntimeError("boom")

    monkeypatch.setattr(client, "_create_completion", _fake_create_completion)

    queries, mode, error = await client.build_search_queries_with_meta(description="school comedy")

    assert queries == ["school comedy"]
    assert mode == "fallback_exception"
    assert "RuntimeError" in error


async def test_huggingface_llm_client_returns_fallback_taste_summary_without_api_key():
    """Проверяем, что описание вкуса возвращает fallback без API key."""
    client = HuggingFaceLLMClient(api_key=None, model="model", provider="provider")

    result = await client.describe_taste_profile(
        profile_data={"mood": "Боевой драйв"},
        fallback="fallback summary",
    )

    assert result == "fallback summary"


async def test_huggingface_llm_client_builds_taste_summary_from_completion(monkeypatch):
    """Проверяем, что описание вкуса берется из completion, если модель ответила валидным текстом."""
    client = HuggingFaceLLMClient(api_key="token", model="model", provider="provider")

    async def _fake_completion_with_timeout(model_route, messages, timeout_seconds):
        return {
            "choices": [{"message": {"content": "Ты любишь экшен с сильным темпом."}}]
        }

    monkeypatch.setattr(client, "_create_completion_with_timeout", _fake_completion_with_timeout)

    result = await client.describe_taste_profile(
        profile_data={"mood": "Боевой драйв"},
        fallback="fallback summary",
    )

    assert result == "Ты любишь экшен с сильным темпом."
