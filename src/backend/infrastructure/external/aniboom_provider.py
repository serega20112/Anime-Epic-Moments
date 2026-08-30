import html as html_mod
import logging
import re

import httpx

from backend.domain.value_objects.watch.discovery import DiscoveredWatchSource
from backend.infrastructure.external.errors import (
    ExternalServiceInvalidResponseError,
    ExternalServiceTimeoutError,
    ExternalServiceUnavailableError,
)
from backend.infrastructure.external.watch_source_provider import WatchSourceProvider

logger = logging.getLogger(__name__)

_DATA_PARAMETERS_RE = re.compile(
    r'<div[^>]*id=["\']video["\'][^>]*data-parameters=["\']([^"\']*)["\']',
    re.IGNORECASE,
)
_HLS_SRC_RE = re.compile(r'"hls":"\{"src":"(https?[^"]*?\.m3u8)"', re.IGNORECASE)
_DASH_SRC_RE = re.compile(r'"dash":"\{"src":"(https?[^"]*?\.(?:mpd|m3u8))"', re.IGNORECASE)


class AniBoomProvider(WatchSourceProvider):
    """Извлекает HLS/MPD-источники AniBoom из embed-страницы плеера.

    Провайдер получает готовую конфигурацию через DI и не читает окружение
    напрямую. Транспортные сбои транслируются в
    :mod:`backend.infrastructure.external.errors`.
    """

    def __init__(self, *, base_url: str, enabled: bool, timeout: float):
        self.base_url = base_url.rstrip("/")
        self.enabled = enabled
        self.timeout = timeout
        self.provider_name = "AniBoom"
        self.session = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            trust_env=False,
            follow_redirects=True,
        )
        self._fetch_headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Referer": "https://animego.me/",
        }
        self.video_headers = {
            "Referer": f"{self.base_url}/",
            "Accept-Language": "ru-RU",
            "Origin": self.base_url,
        }

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
        limit: int = 8,
        shikimori_id: int | None = None,
    ) -> list[DiscoveredWatchSource]:
        """Поиск по тайтлу.

        В эталонной реализации (anicli-api) AniBoom не имеет публичного
        поискового индекса: это extractor, который работает от embed-URL
        (обычно выдаётся catalогу вроде animego). Поэтому по одному тайтлу
        источник не находится, а рабочий путь — `extract_embed`.
        """
        return []

    async def extract_embed(self, embed_url: str, episode: int = 1) -> list[DiscoveredWatchSource]:
        """Извлекает доступные видео-источники из embed-страницы AniBoom.

        Args:
            embed_url: URL вида {base}/embed/<id>?episode=N&translation=T.
            episode: Номер эпизода для результата.

        Returns:
            list[DiscoveredWatchSource]: Найденные источники (HLS, при его
            отсутствии — DASH).
        """
        page_text = await self._fetch(embed_url)

        clean = await self._clean_params(page_text)
        hls = _HLS_SRC_RE.search(clean)
        dash = _DASH_SRC_RE.search(clean)

        stream_urls: list[str] = []
        if hls:
            stream_urls.append(hls.group(1))
        elif dash:
            stream_urls.append(dash.group(1))

        discovered: list[DiscoveredWatchSource] = []
        seen: set[str] = set()
        for stream_url in stream_urls:
            if stream_url in seen:
                continue
            seen.add(stream_url)
            discovered.append(
                DiscoveredWatchSource(
                    episode=episode,
                    translation_name=self.provider_name,
                    translation_type="voice",
                    provider_name=self.provider_name,
                    source_name="aniboom-embed",
                    quality_label="1080",
                    stream_url=stream_url,
                )
            )
        return discovered

    async def _clean_params(self, page_text: str) -> str:
        match = _DATA_PARAMETERS_RE.search(page_text)
        if not match:
            raise ExternalServiceInvalidResponseError(service_name=self.provider_name)
        return html_mod.unescape(match.group(1)).replace("\\", "")

    async def _fetch(self, url: str) -> str:
        try:
            response = await self.session.get(url, headers=self._fetch_headers)
            response.raise_for_status()
            return response.text
        except httpx.TimeoutException as exc:
            raise ExternalServiceTimeoutError(service_name=self.provider_name) from exc
        except httpx.HTTPError as exc:
            raise ExternalServiceUnavailableError(service_name=self.provider_name) from exc
