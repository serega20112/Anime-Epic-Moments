import re
import requests


class HuggingFaceLLMClient:
    """Клиент Hugging Face Inference API для подготовки поискового запроса."""

    _GENERIC_TITLE_MARKERS = (
        "anime",
        "series",
        "show",
        "episodes",
        "daily",
        "frequent",
        "lighthearted",
        "cute",
        "party",
        "scenes",
        "with",
        "about",
    )

    def __init__(
        self,
        api_key: str | None,
        model: str,
        provider: str | None = None,
        api_url: str = "https://router.huggingface.co/v1/chat/completions",
    ):
        self.api_key = api_key
        self.model = model
        self.provider = provider
        self.api_url = api_url

    def build_search_query(
        self,
        description: str,
        genre_hint: str | None = None,
        year_from: int | None = None,
        year_to: int | None = None,
        min_rating: int | None = None,
        allow_adult: bool = False,
    ) -> str:
        """Возвращает краткий англоязычный запрос для AniList по описанию пользователя."""
        query, _, _ = self.build_search_query_with_meta(
            description=description,
            genre_hint=genre_hint,
            year_from=year_from,
            year_to=year_to,
            min_rating=min_rating,
            allow_adult=allow_adult,
        )
        return query

    def build_search_query_with_meta(
        self,
        description: str,
        genre_hint: str | None = None,
        year_from: int | None = None,
        year_to: int | None = None,
        min_rating: int | None = None,
        allow_adult: bool = False,
    ) -> tuple[str, str, str | None]:
        """Возвращает запрос и метаданные режима: hf_llm или fallback_*."""
        queries, mode, error = self.build_search_queries_with_meta(
            description=description,
            genre_hint=genre_hint,
            year_from=year_from,
            year_to=year_to,
            min_rating=min_rating,
            allow_adult=allow_adult,
        )
        first = queries[0] if queries else ""
        return first, mode, error

    def build_search_queries_with_meta(
        self,
        description: str,
        genre_hint: str | None = None,
        year_from: int | None = None,
        year_to: int | None = None,
        min_rating: int | None = None,
        allow_adult: bool = False,
    ) -> tuple[list[str], str, str | None]:
        """Возвращает несколько вариантов поискового запроса и метаданные режима."""
        base_description = description.strip()
        if not base_description:
            return [], "fallback_empty", None
        if not self.api_key:
            fallback_query = self._fallback_query(
                base_description, genre_hint, year_from, year_to, min_rating
            )
            return [fallback_query], "fallback_no_token", None

        user_payload = self._build_user_payload(
            description=base_description,
            genre_hint=genre_hint,
            year_from=year_from,
            year_to=year_to,
            min_rating=min_rating,
            allow_adult=allow_adult,
        )
        messages = [
            {
                "role": "system",
                "content": (
                    "Ты помощник по определению аниме по описанию. "
                    "Верни РОВНО 3 наиболее вероятных названия аниме, каждое на новой строке. "
                    "Только названия, без объяснений, без нумерации, без JSON. "
                    "Не перефразируй описание и не придумывай детали сюжета. "
                    "Не возвращай общие фразы типа 'anime with ...'. "
                    "Если allow_adult=false, не подставляй 18+ термины (hentai/ecchi/porn/nsfw). "
                    "Если уверенность низкая, все равно верни 3 наиболее вероятных тайтла."
                ),
            },
            {"role": "user", "content": user_payload},
        ]

        try:
            model_route = self._resolve_model_route()
            completion = self._create_completion(
                model_route=model_route, messages=messages
            )
            message_content = self._extract_message_content(completion)
            if not message_content:
                fallback_query = self._fallback_query(
                    base_description, genre_hint, year_from, year_to, min_rating
                )
                return [fallback_query], "fallback_empty_reply", None
            parsed_queries = self._parse_queries(message_content)
            if parsed_queries:
                return parsed_queries, "hf_llm_text", None
        except Exception as exc:
            fallback_query = self._fallback_query(
                base_description, genre_hint, year_from, year_to, min_rating
            )
            return (
                [fallback_query],
                "fallback_exception",
                f"{type(exc).__name__}: {exc}",
            )

        fallback_query = self._fallback_query(
            base_description, genre_hint, year_from, year_to, min_rating
        )
        return [fallback_query], "fallback_invalid_json", None

    def _fallback_query(
        self,
        description: str,
        genre_hint: str | None = None,
        year_from: int | None = None,
        year_to: int | None = None,
        min_rating: int | None = None,
    ) -> str:
        """Собирает запасной поисковый запрос без использования LLM."""
        parts = [description.strip()]
        if genre_hint and genre_hint.strip():
            parts.append(genre_hint.strip())
        return " ".join(parts).strip()

    def _build_user_payload(
        self,
        description: str,
        genre_hint: str | None,
        year_from: int | None,
        year_to: int | None,
        min_rating: int | None,
        allow_adult: bool,
    ) -> str:
        """Готовит компактный текстовый payload на русском без JSON-обертки."""
        parts = [
            f"description: {description}",
            f"genre_hint: {genre_hint.strip() if genre_hint else '-'}",
            f"year_from: {year_from if year_from is not None else '-'}",
            f"year_to: {year_to if year_to is not None else '-'}",
            f"min_rating: {min_rating if min_rating is not None else '-'}",
            f"allow_adult: {str(allow_adult).lower()}",
        ]
        return "\n".join(parts)

    def _resolve_model_route(self) -> str:
        """Возвращает model route в формате repo[:provider]."""
        raw_model = self.model.strip()
        if ":" in raw_model:
            return raw_model
        if self.provider:
            return f"{raw_model}:{self.provider.strip()}"
        return raw_model

    def _create_completion(self, model_route: str, messages: list[dict]) -> dict:
        """Отправляет запрос в Hugging Face Router и возвращает JSON-ответ."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "messages": messages,
            "model": model_route,
            "max_tokens": 300,
            "temperature": 0.1,
            "reasoning_effort": "low",
        }
        response = requests.post(
            self.api_url, headers=headers, json=payload, timeout=30
        )
        response.raise_for_status()
        return response.json()

    def _extract_message_content(self, completion: dict) -> str:
        """Извлекает content из HF chat completion JSON."""
        choices = completion.get("choices") if isinstance(completion, dict) else None
        if not isinstance(choices, list) or not choices:
            return ""
        first_choice = choices[0]
        if not isinstance(first_choice, dict):
            return ""
        message = first_choice.get("message", {})
        if not isinstance(message, dict):
            return ""
        content = message.get("content")
        if content:
            return str(content).strip()
        reasoning_content = message.get("reasoning_content")
        if reasoning_content:
            return str(reasoning_content).strip()
        return ""

    def _parse_queries(self, raw_content: str) -> list[str]:
        """Парсит несколько запросов из текста модели (по строкам)."""
        lines = []
        for raw_line in str(raw_content).splitlines():
            line = raw_line.strip().strip("-*• ").strip()
            if not line:
                continue
            if ". " in line and line[:2].isdigit():
                line = line.split(". ", 1)[1].strip()
            normalized_line = " ".join(line.split())
            if not self._looks_like_title_candidate(normalized_line):
                continue
            lines.append(normalized_line)
        unique: list[str] = []
        seen: set[str] = set()
        for line in lines:
            key = line.lower()
            if key == "none" or key in seen:
                continue
            seen.add(key)
            unique.append(line)
            if len(unique) >= 3:
                break
        return unique

    def _looks_like_title_candidate(self, value: str) -> bool:
        """Отбрасывает заведомо не-title строки."""
        if not value:
            return False
        lowered = value.lower().strip()
        if len(lowered) < 2 or len(lowered) > 80:
            return False
        if lowered.startswith("{") or lowered.startswith("["):
            return False
        words = re.findall(r"[a-zA-Zа-яА-Я0-9+'-]+", lowered)
        if not words:
            return False
        if len(words) > 7:
            return False
        if any(marker in lowered for marker in self._GENERIC_TITLE_MARKERS):
            return False
        return True
