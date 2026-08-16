"""Google Gemini LLM client with the same query-building contract as the HF client."""

from __future__ import annotations

from backend.infrastructure.external.huggingface_llm_client import HuggingFaceLLMClient


class GoogleGeminiLLMClient(HuggingFaceLLMClient):
    """Gemini `generateContent` client reusing the shared prompt parsing logic."""

    def __init__(
        self,
        api_key: str | None,
        model: str,
        api_url: str = "https://generativelanguage.googleapis.com/v1beta",
    ):
        super().__init__(api_key=api_key, model=model, provider=None, api_url=api_url)
        self._success_mode = "gemini_llm_text"

    def _create_completion_with_timeout(
        self,
        model_route: str,
        messages: list[dict],
        timeout_seconds: float | int,
    ) -> dict:
        """Send a chat-style request to the Gemini generateContent endpoint.

        Args:
            model_route: Gemini model identifier.
            messages: OpenAI-style messages list to translate.
            timeout_seconds: Request timeout in seconds.

        Returns:
            dict: Raw Gemini response JSON.

        Raises:
            requests.HTTPError: When Gemini returns a non-2xx status.
        """
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
        response = self.session.post(
            url,
            json=payload,
            timeout=timeout_seconds,
        )
        response.raise_for_status()
        return response.json()

    def _extract_message_content(self, completion: dict) -> str:
        """Extract the concatenated text from a Gemini response.

        Args:
            completion: Raw Gemini response JSON.

        Returns:
            str: Extracted text or empty string.
        """
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

    def _resolve_model_route(self) -> str:
        """Return the model identifier ready for the generateContent URL."""
        return self.model.strip().removeprefix("models/").strip()
