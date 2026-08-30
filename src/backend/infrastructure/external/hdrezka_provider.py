import html as html_mod
import re

import httpx

from backend.domain.value_objects.watch.discovery import DiscoveredWatchSource
from backend.infrastructure.external.errors import (
    ExternalServiceTimeoutError,
    ExternalServiceUnavailableError,
)
from backend.infrastructure.external.watch_source_provider import WatchSourceProvider

_SEARCH_RESULT_RE = re.compile(
    r"href=\"(?:https?:)?//[^\"]*?/anime/[^\"]*?-i(\d+)\.html\"", re.IGNORECASE
)
_TRANSLATOR_RE = re.compile(
    r"data-translator_id=\"(\d+)\"[^>]*>\s*(?:<[^>]+>\s*)*([^<]+)", re.IGNORECASE
)
_LINK_ENTRY_RE = re.compile(r"\[(\d+p)\]((?:https?:)?//[^,\s]+)", re.IGNORECASE)


class HDRezkaProvider(WatchSourceProvider):
    """Парсер HDRezka (voidboost): прямые HLS/MP4 без токенов.

    Best-effort реализация: сайт часто меняет защиту и включает шифрование
    ссылок (``encrypted``) — в этом случае провайдер честно не возвращает
    источников. Провайдер получает готовую конфигурацию через DI и по
    умолчанию выключен.
    """

    def __init__(self, *, base_url: str, enabled: bool, timeout: float):
        self.base_url = base_url.rstrip("/")
        self.enabled = enabled
        self.timeout = timeout
        self.provider_name = "HDRezka"
        self.session = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            trust_env=False,
            follow_redirects=True,
            headers={
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "X-Requested-With": "XMLHttpRequest",
                "Referer": f"{self.base_url}/",
            },
        )

    async def aclose(self) -> None:
        """Close the underlying HTTP client."""
        await self.session.aclose()

    async def is_enabled(self) -> bool:
        return bool(self.enabled and self.base_url)

    async def search_sources(
        self,
        title: str,
        episode: int,
        year: int | None = None,
        limit: int = 1,
        shikimori_id: int | None = None,
    ) -> list[DiscoveredWatchSource]:
        """Ищет источники эпизода на HDRezka.

        Args:
            title: Название аниме для поиска.
            episode: Номер эпизода.
            year: Год релиза (не используется HDRezka).
            limit: Максимум обрабатываемых страниц тайтла.
            shikimori_id: Внешний id тайтла (игнорируется: у HDRezka свой id).

        Returns:
            list[DiscoveredWatchSource]: Прямые потоки по качествам и озвучкам.
        """
        if not await self.is_enabled():
            return []

        content_ids = await self._search_content_ids(title, limit=limit)
        discovered: list[DiscoveredWatchSource] = []
        seen: set[str] = set()
        for content_id in content_ids:
            translators = await self._get_translators(content_id)
            for translator_id, translator_name in translators or [("0", "HDRezka")]:
                links = await self._request_streams(
                    content_id=content_id, translator_id=translator_id
                )
                for quality_label, stream_url in links:
                    dedupe_key = (translator_name, quality_label, stream_url)
                    if dedupe_key in seen:
                        continue
                    seen.add(dedupe_key)
                    discovered.append(
                        DiscoveredWatchSource(
                            episode=episode,
                            translation_name=translator_name,
                            translation_type="voice",
                            provider_name=self.provider_name,
                            source_name=f"rezka-{content_id}",
                            quality_label=quality_label,
                            source_type="stream",
                            stream_url=stream_url,
                        )
                    )
        return discovered

    async def _search_content_ids(self, title: str, limit: int) -> list[str]:
        page_text = await self._fetch(
            f"{self.base_url}/search/", params={"do": "search", "q": title}
        )
        ids: list[str] = []
        for match in _SEARCH_RESULT_RE.finditer(page_text):
            content_id = match.group(1)
            if content_id not in ids:
                ids.append(content_id)
            if len(ids) >= max(int(limit), 1):
                break
        return ids

    async def _get_translators(self, content_id: str) -> list[tuple[str, str]] | None:
        page_text = await self._fetch(f"{self.base_url}/anime/{content_id}")
        translators: list[tuple[str, str]] = []
        seen: set[str] = set()
        for match in _TRANSLATOR_RE.finditer(page_text):
            translator_id = match.group(1)
            if translator_id in seen:
                continue
            name = html_mod.unescape(match.group(2)).strip()
            if not name:
                continue
            seen.add(translator_id)
            translators.append((translator_id, name))
        return translators or None

    async def _request_streams(
        self, *, content_id: str, translator_id: str
    ) -> list[tuple[str, str]]:
        try:
            response = await self.session.post(
                f"{self.base_url}/ajax/get_cdn_series/",
                data={
                    "id": content_id,
                    "translator_id": translator_id,
                    "is_camrip": "0",
                    "is_director": "0",
                    "is_ads": "0",
                    "is_voiceover": "0",
                    "action": "get_stream",
                },
            )
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError):
            return []

        message = payload.get("message") if isinstance(payload, dict) else None
        if not isinstance(message, dict):
            return []
        if str(message.get("encrypted") or "") == "1":
            return []

        raw_links = str(message.get("links") or "")
        results: list[tuple[str, str]] = []
        seen: set[str] = set()
        for match in _LINK_ENTRY_RE.finditer(raw_links):
            quality_label = match.group(1).lower()
            stream_url = await self._ensure_https(match.group(2))
            if stream_url in seen or not stream_url:
                continue
            seen.add(stream_url)
            results.append((quality_label, stream_url))
        return results

    @staticmethod
    async def _ensure_https(url: str) -> str:
        text = str(url).strip()
        if text.startswith("//"):
            return f"https:{text}"
        return text

    async def _fetch(self, url: str, params: dict | None = None) -> str:
        try:
            response = await self.session.get(url, params=params)
            response.raise_for_status()
            return response.text
        except httpx.TimeoutException as exc:
            raise ExternalServiceTimeoutError(service_name=self.provider_name) from exc
        except httpx.HTTPError as exc:
            raise ExternalServiceUnavailableError(service_name=self.provider_name) from exc
