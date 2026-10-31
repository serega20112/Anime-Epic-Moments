"""LLM-клиенты поиска аниме по описанию и их отказоустойчивая обвязка.

Подпакет закрывает порт `LLMClientInterface` из application-слоя:

- `google_gemini_llm_client` — основной провайдер;
- `huggingface_llm_client` и `openrouter_llm_client` — запасные;
- `failover_llm_client` — последовательный перебор с сохранением причины отказа каждого
  провайдера.

Ключи и включение провайдеров приходят из `config.sections.external`; решение «кого
звать первым» принимается здесь, а не в сценариях.
"""

from __future__ import annotations

from .failover_llm_client import FailoverLLMClient
from .google_gemini_llm_client import GoogleGeminiLLMClient
from .huggingface_llm_client import HuggingFaceLLMClient
from .openrouter_llm_client import DEFAULT_OPENROUTER_API_URL, OpenRouterLLMClient

__all__ = [
    "DEFAULT_OPENROUTER_API_URL",
    "FailoverLLMClient",
    "GoogleGeminiLLMClient",
    "HuggingFaceLLMClient",
    "OpenRouterLLMClient",
]
