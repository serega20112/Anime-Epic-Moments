"""LLM-клиент OpenRouter (OpenAI-совместимый chat completions)."""

from __future__ import annotations

import httpx

from backend.infrastructure.external.huggingface_llm_client import HuggingFaceLLMClient

DEFAULT_OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"


class OpenRouterLLMClient(HuggingFaceLLMClient):
    """Клиент OpenRouter.

    Провайдер использует тот же OpenAI-совместимый формат запроса, что и
    Hugging Face Router, поэтому переиспользуется вся логика построения
    поисковых запросов; модель передаётся как есть (vendor/model),
    без HF-суффикса провайдера.

    Отличия от родителя:
    - reasoning-моделям запрещено возвращать рассуждения в ответе
      (``reasoning.exclude``), иначе ``content`` остаётся пустым;
    - повышен ``max_tokens``, т.к. часть бюджета уходит в рассуждения;
    - если модель всё же вернула только reasoning, текст извлекается из него.
    """

    _success_mode = "openrouter_llm_text"

    def __init__(
        self,
        api_key: str | None,
        model: str,
        api_url: str = DEFAULT_OPENROUTER_API_URL,
    ):
        super().__init__(api_key=api_key, model=model, provider=None, api_url=api_url)
        self._success_mode = "openrouter_llm_text"
        self.session = httpx.AsyncClient(
            timeout=httpx.Timeout(30),
            trust_env=True,
            follow_redirects=True,
        )

    async def _create_completion_with_timeout(
        self,
        model_route: str,
        messages: list[dict],
        timeout_seconds: float | int,
    ) -> dict:
        """Отправляет запрос в OpenRouter с настройками для reasoning-моделей."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "messages": messages,
            "model": model_route,
            "max_tokens": 900,
            "temperature": 0.1,
            "reasoning": {"exclude": True},
        }
        response = await self.session.post(
            self.api_url, headers=headers, json=payload, timeout=timeout_seconds
        )
        response.raise_for_status()
        return response.json()

    async def _extract_message_content(self, completion: dict) -> str:
        """Извлекает content; для reasoning-моделей — текст из поля reasoning."""
        content = await super()._extract_message_content(completion)
        if content:
            return content
        choices = completion.get("choices") if isinstance(completion, dict) else None
        if not isinstance(choices, list) or not choices:
            return ""
        first_choice = choices[0]
        if not isinstance(first_choice, dict):
            return ""
        message = first_choice.get("message", {})
        if not isinstance(message, dict):
            return ""
        reasoning = message.get("reasoning")
        if isinstance(reasoning, str) and reasoning.strip():
            return reasoning.strip()
        return ""
