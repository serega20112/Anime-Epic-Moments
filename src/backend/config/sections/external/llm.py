"""Настройки LLM-провайдеров поиска по описанию: HF, OpenRouter, Google."""

from __future__ import annotations

import os


def hf_token() -> str | None:
    """Вернуть токен Hugging Face API или None."""
    return os.getenv("HF_TOKEN")


def hf_provider() -> str | None:
    """Вернуть имя провайдера Hugging Face."""
    return os.getenv("HF_PROVIDER", "fireworks-ai")


def hf_model() -> str:
    """Вернуть идентификатор модели Hugging Face."""
    return os.getenv("HF_MODEL", "openai/gpt-oss-120b")


def hf_api_url() -> str:
    """Вернуть адрес chat completions Hugging Face."""
    return os.getenv("HF_API_URL", "https://router.huggingface.co/v1/chat/completions")


def openrouter_api_key() -> str | None:
    """Вернуть ключ OpenRouter API или None."""
    value = os.getenv("OPENROUTER_API_KEY", "").strip()
    return value or None


def openrouter_model() -> str:
    """Вернуть идентификатор модели OpenRouter в виде ``vendor/model``."""
    return os.getenv("OPENROUTER_MODEL", "openrouter/auto")


def openrouter_api_url() -> str:
    """Вернуть адрес chat completions OpenRouter."""
    return os.getenv("OPENROUTER_API_URL", "https://openrouter.ai/api/v1/chat/completions")


def google_api_key() -> str | None:
    """Вернуть ключ Google Gemini API или None."""
    return os.getenv("GOOGLE_API_KEY")


def google_model() -> str:
    """Вернуть идентификатор модели Google Gemini."""
    return os.getenv("GOOGLE_MODEL", "gemini-2.0-flash")


def google_api_url() -> str:
    """Вернуть базовый адрес Google Gemini API."""
    return os.getenv("GOOGLE_API_URL", "https://generativelanguage.googleapis.com/v1beta")
