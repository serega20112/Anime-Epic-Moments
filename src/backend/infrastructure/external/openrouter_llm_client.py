"""LLM-клиент OpenRouter (OpenAI-совместимый chat completions)."""

from __future__ import annotations

from backend.infrastructure.external.huggingface_llm_client import HuggingFaceLLMClient

DEFAULT_OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"


class OpenRouterLLMClient(HuggingFaceLLMClient):
    """Клиент OpenRouter.

    Провайдер использует тот же OpenAI-совместимый формат запроса, что и
    Hugging Face Router, поэтому переиспользуется вся логика построения
    поисковых запросов; модель передаётся как есть (vendor/model),
    без HF-суффикса провайдера.
    """

    _success_mode = "openrouter_llm_text"

    def __init__(
        self,
        api_key: str | None,
        model: str,
        api_url: str = DEFAULT_OPENROUTER_API_URL,
    ):
        super().__init__(api_key=api_key, model=model, provider=None, api_url=api_url)
        # родитель выставляет _success_mode в __init__ — переопределяем после
        self._success_mode = "openrouter_llm_text"
