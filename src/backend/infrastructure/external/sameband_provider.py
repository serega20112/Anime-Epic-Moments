import json
import logging
import re

import httpx

from backend.domain.watch.value_object import DiscoveredWatchSource
from backend.infrastructure.external.errors import (
    ExternalServiceInvalidResponseError,
    ExternalServiceTimeoutError,
    ExternalServiceUnavailableError,
)
from backend.infrastructure.external.watch_source_provider import WatchSourceProvider

logger = logging.getLogger(__name__)

_PLAYER_JS_RE = re.compile(r"Playerjs[^>]+file:\s*[\"\']([^>]+)[\"\']", re.IGNORECASE)
_IFRAME_SRC_RE = re.compile(r'<iframe[^>]*src=["\']([^"\']+)["\']', re.IGNORECASE)
_QUALITY_ENTRY_RE = re.compile(r"\[(\d+)p\](.*)", re.IGNORECASE)
_COLUMN_SPLIT_RE = re.compile(r'class=["\']col-auto["\']', re.IGNORECASE)
_HREF_RE = re.compile(r'href=["\']([^"\']+)["\']', re.IGNORECASE)
_FILE_JSON_RE = re.compile(r'"file"\s*:\s*"((?:[^"\\]|\\.)*)"', re.IGNORECASE)

_BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ru-RU,en;q=0.8",
}


class SamebandProvider(WatchSourceProvider):
    """Ищет релизы SameBand (SSR) и извлекает HLS-источники по эпизодам.

    Провайдер получает готовую конфигурацию через DI и не читает окружение
    напрямую. Сайт закрыт Cloudflare-защитой, поэтому используется асинхронный
    HTTP-клиент httpx с браузерными заголовками. Транспортные сбои и
    malformed-ответы транслируются в
    :mod:`backend.infrastructure.external.errors`.
    """

    def __init__(self, *, base_url: str, enabled: bool, timeout: float):
        self.base_url = base_url.rstrip("/")
        self.enabled = enabled
        self.timeout = timeout
        self.provider_name = "SameBand"
        self._session = httpx.AsyncClient(
            headers={**_BROWSER_HEADERS, "Referer": self.base_url},
            timeout=httpx.Timeout(timeout),
            trust_env=False,
            follow_redirects=True,
        )

    async def aclose(self) -> None:
        """Close the underlying HTTP client."""
        await self._session.aclose()

    async def is_enabled(self) -> bool:
        return bool(self.enabled and self.base_url)

    async def search_sources(
        self,
        title: str,
        episode: int,
        year: int | None = None,
        limit: int = 8,
    ) -> list[DiscoveredWatchSource]:
        """Ищет источники для конкретного аниме и эпизода.

        Args:
            title: Название аниме для поиска.
            episode: Номер эпизода.
            year: Год релиза (не используется SameBand).
            limit: Максимальное число обрабатываемых релизов.

        Returns:
            list[DiscoveredWatchSource]: Найденные источники.
        """
        if not await self.is_enabled():
            return []

        anime_urls = await self._search(title, limit=limit)
        discovered: list[DiscoveredWatchSource] = []
        seen: set[tuple[str, str]] = set()
        for anime_url in anime_urls:
            playlist = await self._get_playlist(anime_url)
            if not playlist:
                continue
            qualities = await self._episode_qualities(playlist, episode=episode)
            if not qualities:
                continue
            for quality_label, stream_url in qualities:
                dedupe_key = (quality_label, stream_url)
                if dedupe_key in seen:
                    continue
                seen.add(dedupe_key)
                discovered.append(
                    DiscoveredWatchSource(
                        episode=episode,
                        translation_name=self.provider_name,
                        translation_type="voice",
                        provider_name=self.provider_name,
                        source_name=f"sameband-ep{episode}",
                        quality_label=quality_label,
                        stream_url=stream_url,
                    )
                )
        return discovered

    async def _search(self, title: str, limit: int) -> list[str]:
        try:
            response = await self._session.get(
                f"{self.base_url}/index.php",
                params={
                    "do": "search",
                    "subaction": "search",
                    "search_start": "0",
                    "full_search": "0",
                    "story": title,
                },
            )
            response.raise_for_status()
            page_text = response.text
        except httpx.TimeoutException as exc:
            raise ExternalServiceTimeoutError(service_name=self.provider_name) from exc
        except httpx.HTTPError as exc:
            raise ExternalServiceUnavailableError(service_name=self.provider_name) from exc

        urls: list[str] = []
        seen: set[str] = set()
        for chunk in _COLUMN_SPLIT_RE.split(page_text):
            match = _HREF_RE.search(chunk)
            if not match:
                continue
            href = await self._to_absolute(match.group(1))
            if "/anime/" not in href or href in seen:
                continue
            seen.add(href)
            urls.append(href)
        return urls[: max(int(limit), 1)]

    async def _get_playlist(self, anime_url: str) -> list[dict] | None:
        page_text = await self._fetch(anime_url)

        iframes = _IFRAME_SRC_RE.findall(page_text)
        if not iframes:
            return None
        player_url = await self._to_absolute(iframes[-1])

        player_text = await self._fetch(player_url)
        match = _PLAYER_JS_RE.search(player_text)
        if not match:
            raise ExternalServiceInvalidResponseError(service_name=self.provider_name)
        playlist_url = await self._to_absolute(match.group(1))

        return await self._parse_playlist(await self._fetch(playlist_url))

    async def _parse_playlist(self, text: str) -> list[dict]:
        try:
            payload = json.loads(text)
            if isinstance(payload, list):
                return [item for item in payload if isinstance(item, dict) and item.get("file")]
        except (ValueError, TypeError):
            pass
        matches = [match.group(1) for match in _FILE_JSON_RE.finditer(text) if match.group(1)]
        if not matches and text.strip():
            raise ExternalServiceInvalidResponseError(service_name=self.provider_name)
        return [{"file": value} for value in matches]

    async def _episode_qualities(self, playlist: list[dict], episode: int) -> list[tuple[str, str]]:
        index = int(episode) - 1
        if index < 0 or index >= len(playlist):
            return []
        file_value = str(playlist[index].get("file") or "")
        qualities: list[tuple[str, str]] = []
        seen: set[str] = set()
        for entry in file_value.split(","):
            entry_match = _QUALITY_ENTRY_RE.match(entry.strip())
            if not entry_match:
                continue
            quality_label = f"{entry_match.group(1)}p"
            stream_url = await self._to_absolute(entry_match.group(2))
            if quality_label in seen or not stream_url:
                continue
            seen.add(quality_label)
            qualities.append((quality_label, stream_url))
        return qualities

    async def _fetch(self, url: str) -> str:
        try:
            response = await self._session.get(url)
            response.raise_for_status()
            return response.text
        except httpx.TimeoutException as exc:
            raise ExternalServiceTimeoutError(service_name=self.provider_name) from exc
        except httpx.HTTPError as exc:
            raise ExternalServiceUnavailableError(service_name=self.provider_name) from exc

    async def _to_absolute(self, value: str | None) -> str:
        if not value:
            return ""
        text = str(value).strip()
        if text.startswith("//"):
            return f"https:{text}"
        if text.startswith("/"):
            return f"{self.base_url}{text}"
        return text
