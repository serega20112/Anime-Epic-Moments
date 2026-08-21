import re

import httpx

from backend.config import Settings
from backend.domain.policies.watch_policy import canonicalize_translation_name
from backend.domain.value_objects.watch.discovery import DiscoveredWatchSource
from backend.infrastructure.external.watch_source_provider import WatchSourceProvider


class YouTubeClient(WatchSourceProvider):
    """Ищет embeddable-видео на YouTube по названию тайтла и номеру эпизода."""

    def __init__(self):
        self.api_key = Settings.youtube_api_key
        self.api_url = Settings.youtube_api_url.rstrip("/")
        self.allowed_channel_ids = set(Settings.youtube_allowed_channel_ids)
        self.provider_name = "YouTube"
        self.session = httpx.AsyncClient(
            timeout=httpx.Timeout(6),
            trust_env=False,
            follow_redirects=True,
        )

    async def is_enabled(self) -> bool:
        """Возвращает доступность YouTube-провайдера."""
        return bool(self.api_key)

    async def aclose(self) -> None:
        """Close the underlying HTTP client."""
        await self.session.aclose()

    async def search_sources(
        self,
        title: str,
        episode: int,
        year: int | None = None,
        limit: int = 6,
    ) -> list[DiscoveredWatchSource]:
        """Ищет embeddable-источники YouTube для конкретного эпизода."""
        if not await self.is_enabled():
            return []

        candidates: list[tuple[int, DiscoveredWatchSource]] = []
        seen_urls: set[str] = set()
        for query in await self._build_queries(title=title, episode=episode, year=year):
            for item in await self._search_videos(query=query, limit=limit):
                mapped = await self._map_video(
                    payload=item,
                    requested_title=title,
                    requested_episode=episode,
                )
                if not mapped:
                    continue
                score, source = mapped
                if source.stream_url in seen_urls:
                    continue
                seen_urls.add(source.stream_url)
                candidates.append((score, source))
        candidates.sort(
            key=lambda item: (
                -item[0],
                item[1].translation_name.lower(),
                item[1].source_name.lower(),
            )
        )
        return [item[1] for item in candidates[:limit]]

    async def _build_queries(self, title: str, episode: int, year: int | None) -> list[str]:
        """Формирует поисковые запросы YouTube для эпизода."""
        base_title = str(title or "").strip()
        if not base_title:
            return []
        queries = [
            f'"{base_title}" {episode} серия',
            f'"{base_title}" episode {episode}',
        ]
        if year:
            queries.append(f'"{base_title}" {year} {episode} серия')
        seen: set[str] = set()
        unique_queries: list[str] = []
        for item in queries:
            normalized = " ".join(item.split())
            if normalized in seen:
                continue
            seen.add(normalized)
            unique_queries.append(normalized)
        return unique_queries

    async def _search_videos(self, query: str, limit: int) -> list[dict]:
        """Выполняет поиск embeddable-видео через YouTube Data API."""
        try:
            response = await self.session.get(
                f"{self.api_url}/search",
                params={
                    "key": self.api_key or "",
                    "part": "snippet",
                    "type": "video",
                    "videoEmbeddable": "true",
                    "safeSearch": "moderate",
                    "relevanceLanguage": "ru",
                    "maxResults": max(min(int(limit), 25), 1),
                    "q": query,
                },
            )
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError, TypeError):
            return []
        items = payload.get("items") or []
        if not isinstance(items, list):
            return []
        if not self.allowed_channel_ids:
            return items
        return [
            item
            for item in items
            if str(item.get("snippet", {}).get("channelId") or "").strip()
            in self.allowed_channel_ids
        ]

    async def _map_video(
        self,
        payload: dict,
        requested_title: str,
        requested_episode: int,
    ) -> tuple[int, DiscoveredWatchSource] | None:
        """Преобразует результат YouTube API в найденный источник с оценкой релевантности."""
        video_id = str(payload.get("id", {}).get("videoId") or "").strip()
        snippet = payload.get("snippet") or {}
        video_title = str(snippet.get("title") or "").strip()
        channel_title = str(snippet.get("channelTitle") or "").strip()
        if not video_id or not video_title:
            return None

        score = await self._score_video(
            video_title=video_title,
            channel_title=channel_title,
            requested_title=requested_title,
            requested_episode=requested_episode,
        )
        if score <= 0:
            return None

        raw_translation = await canonicalize_translation_name(
            f"{video_title} {channel_title}".strip()
        )
        translation_name = (
            raw_translation
            if raw_translation
            and raw_translation not in {video_title, f"{video_title} {channel_title}".strip()}
            else (channel_title or self.provider_name)
        )
        translation_type = (
            "sub"
            if await self._looks_like_subtitles(f"{video_title} {channel_title}".strip())
            else "voice"
        )
        return (
            score,
            DiscoveredWatchSource(
                episode=requested_episode,
                translation_name=translation_name,
                translation_type=translation_type,
                provider_name=self.provider_name,
                source_name=video_title,
                quality_label="YouTube",
                stream_url=(
                    f"https://www.youtube.com/embed/{video_id}?enablejsapi=1&rel=0&modestbranding=1"
                ),
                source_type="embed",
            ),
        )

    async def _score_video(
        self,
        video_title: str,
        channel_title: str,
        requested_title: str,
        requested_episode: int,
    ) -> int:
        """Оценивает релевантность ролика YouTube для конкретного эпизода."""
        normalized_blob = await self._normalize_text(f"{video_title} {channel_title}".strip())
        title_tokens = [
            token
            for token in (await self._normalize_text(requested_title)).split()
            if len(token) > 1
        ]
        if not title_tokens:
            return 0

        matched_tokens = sum(1 for token in title_tokens if token in normalized_blob)
        if matched_tokens == 0:
            return 0

        if not await self._has_episode_marker(normalized_blob, requested_episode):
            return 0

        banned_markers = (
            "trailer",
            "preview",
            "teaser",
            "тизер",
            "трейлер",
            "opening",
            "ending",
            "op ",
            " ed ",
            " amv ",
            " clip ",
            " reaction ",
            " review ",
        )
        if any(marker in f" {normalized_blob} " for marker in banned_markers):
            return 0

        score = matched_tokens * 3
        if matched_tokens == len(title_tokens):
            score += 4
        if await canonicalize_translation_name(normalized_blob) != normalized_blob:
            score += 2
        return score

    async def _has_episode_marker(self, value: str, episode: int) -> bool:
        """Проверяет, упоминается ли нужный эпизод в заголовке или названии канала."""
        episode_patterns = (
            rf"(?:episode|ep|серия|сер|сер\.|выпуск)\s*0*{episode}(?!\d)",
            rf"\b0*{episode}\s*(?:episode|ep|серия|сер|сер\.)\b",
            rf"\b0*{episode}\b",
        )
        return any(re.search(pattern, value, flags=re.IGNORECASE) for pattern in episode_patterns)

    async def _looks_like_subtitles(self, value: str) -> bool:
        """Определяет по тексту, относится ли ролик к субтитрам."""
        normalized = await self._normalize_text(value)
        return any(
            marker in normalized for marker in ("sub", "subs", "subtitles", "суб", "субтитры")
        )

    async def _normalize_text(self, value: str | None) -> str:
        """Нормализует текст для эвристического сравнения."""
        text = str(value or "").lower().strip()
        text = re.sub(r"[^a-zа-я0-9]+", " ", text, flags=re.IGNORECASE)
        return " ".join(text.split())
