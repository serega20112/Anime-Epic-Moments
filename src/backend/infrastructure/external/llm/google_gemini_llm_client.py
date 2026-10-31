"""Клиент Gemini с тем же контрактом построения запросов, что у HF-клиента."""

from __future__ import annotations

from backend.infrastructure.external.llm.huggingface_llm_client import HuggingFaceLLMClient


class GoogleGeminiLLMClient(HuggingFaceLLMClient):
    """Клиент Gemini ``generateContent``, переиспользующий разбор ответа HF-клиента."""

    def __init__(
        self,
        api_key: str | None,
        model: str,
        api_url: str = "https://generativelanguage.googleapis.com/v1beta",
    ):
        """Создать клиент Gemini с ключом, моделью и адресом API."""
        super().__init__(api_key=api_key, model=model, provider=None, api_url=api_url)
        self._success_mode = "gemini_llm_text"

    async def _create_completion_with_timeout(
        self,
        model_route: str,
        messages: list[dict],
        timeout_seconds: float | int,
    ) -> dict:
        """Отправить запрос к методу Gemini ``generateContent``."""
        url = f"{self.api_url}/models/{model_route}:generateContent?key={self.api_key}"
        system_parts: list[str] = []
        contents: list[dict] = []
        for message in messages:
            role = str(message.get("role") or "user")
            text = str(message.get("content") or "")
            if role == "system":
                system_parts.append(text)
                continue
            contents.append(
                {"role": "user" if role != "assistant" else "model", "parts": [{"text": text}]}
            )
        payload: dict = {
            "contents": contents,
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 300,
            },
        }
        if system_parts:
            payload["systemInstruction"] = {"parts": [{"text": text} for text in system_parts]}
        response = await self.session.post(
            url,
            json=payload,
            timeout=timeout_seconds,
        )
        response.raise_for_status()
        return response.json()

    async def _extract_message_content(self, completion: dict) -> str:
        """Извлечь склеенный текст из ответа Gemini."""
        candidates = completion.get("candidates") if isinstance(completion, dict) else None
        if not isinstance(candidates, list) or not candidates:
            return ""
        content = candidates[0].get("content") if isinstance(candidates[0], dict) else None
        if not isinstance(content, dict):
            return ""
        parts = content.get("parts")
        if not isinstance(parts, list):
            return ""
        texts = [
            str(part.get("text") or "")
            for part in parts
            if isinstance(part, dict) and part.get("text")
        ]
        return "\n".join(texts).strip()

    async def _resolve_model_route(self) -> str:
        """Вернуть имя модели, готовое для адреса ``generateContent``."""
        return self.model.strip().removeprefix("models/").strip()
