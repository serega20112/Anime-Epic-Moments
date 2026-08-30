import html as html_mod
import re
from urllib.parse import urlparse

import httpx

from backend.domain.exceptions import ExternalServiceError
from backend.domain.value_objects.watch.discovery import DiscoveredWatchSource
from backend.infrastructure.external.errors import (
    ExternalServiceTimeoutError,
    ExternalServiceUnavailableError,
)
from backend.infrastructure.external.watch_source_provider import WatchSourceProvider

_SEARCH_RESULT_RE = re.compile(
    r"href=\"(?:https?://[^\"]*)?/anime/([^\"]*?-(\d+))(?:\.html)?\"[^>]*>", re.IGNORECASE
)
_TRANSLATOR_RE = re.compile(r"data-translator-id=\"(\d+)\"[^>]*>(.*?)</", re.IGNORECASE | re.DOTALL)
_IFRAME_SRC_RE = re.compile(r"<iframe[^>]*src=[\"']([^\"']+)[\"']", re.IGNORECASE)
_TAG_RE = re.compile(r"<[^>]+>")


class AnimeGoProvider(WatchSourceProvider):
    """Скрейпер агрегатора AnimeGo: озвучки и плееры фандаба.

    AnimeGo — крупнейший каталог русского аниме-фандаба (включая редкие
    любительские озвучки). Провайдер ищет тайтл в каталоге, разбирает вкладки
    озвучек и через внутренний AJAX-эндпоинт получает embed-URL плеера
    эпизода. Извлечение потока делегируется экстракторам:

    - ``video.sibnet.ru`` → Sibnet-экстрактор (прямые MP4);
    - AniBoom → AniBoom-экстрактор (HLS);
    - остальные хосты → отдаются как есть (embed).
    """

    def __init__(
        self,
        *,
        base_url: str,
        enabled: bool,
        timeout: float,
        sibnet_extractor=None,
        aniboom_extractor=None,
    ):
        self.base_url = base_url.rstrip("/")
        self.enabled = enabled
        self.timeout = timeout
        self.provider_name = "AnimeGo"
        self._sibnet_extractor = sibnet_extractor
        self._aniboom_extractor = aniboom_extractor
        self.session = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            trust_env=False,
            follow_redirects=True,
            headers={
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
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
        limit: int = 3,
        shikimori_id: int | None = None,
    ) -> list[DiscoveredWatchSource]:
        """Ищет источники для конкретного аниме и эпизода.

        Args:
            title: Название аниме для поиска.
            episode: Номер эпизода.
            year: Год релиза (не используется AnimeGo).
            limit: Максимум обрабатываемых страниц тайтла.
            shikimori_id: Внешний id тайтла (игнорируется: у AnimeGo свой id).

        Returns:
            list[DiscoveredWatchSource]: Найденные источники по всем озвучкам.
        """
        if not await self.is_enabled():
            return []

        anime_ids = await self._search_anime_ids(title, limit=limit)
        discovered: list[DiscoveredWatchSource] = []
        seen: set[str] = set()
        for anime_id in anime_ids:
            translations = await self._get_translations(anime_id)
            for translator_id, translator_name in translations:
                embed_url = await self._get_episode_embed(
                    anime_id=anime_id,
                    episode=episode,
                    translator_id=translator_id,
                )
                if not embed_url:
                    continue
                items = await self._resolve_embed(embed_url, episode, translator_name)
                for item in items:
                    dedupe_key = (
                        item.translation_name,
                        item.provider_name,
                        item.stream_url,
                    )
                    if dedupe_key in seen:
                        continue
                    seen.add(dedupe_key)
                    discovered.append(item)
        return discovered

    async def _search_anime_ids(self, title: str, limit: int) -> list[str]:
        page_text = await self._fetch(f"{self.base_url}/search/anime", params={"q": title})
        ids: list[str] = []
        for match in _SEARCH_RESULT_RE.finditer(page_text):
            anime_id = match.group(2)
            if anime_id not in ids:
                ids.append(anime_id)
            if len(ids) >= max(int(limit), 1):
                break
        return ids

    async def _get_translations(self, anime_id: str) -> list[tuple[str, str]]:
        page_text = await self._fetch(f"{self.base_url}/anime/{anime_id}")
        translations: list[tuple[str, str]] = []
        seen: set[str] = set()
        for match in _TRANSLATOR_RE.finditer(page_text):
            translator_id = match.group(1)
            if translator_id in seen:
                continue
            name = html_mod.unescape(_TAG_RE.sub("", match.group(2))).strip()
            if not name:
                name = f"Dub {translator_id}"
            seen.add(translator_id)
            translations.append((translator_id, name))
        return translations

    async def _get_episode_embed(
        self, *, anime_id: str, episode: int, translator_id: str
    ) -> str | None:
        payload = None
        try:
            response = await self.session.get(
                f"{self.base_url}/ajax/anime/{anime_id}/episode/{max(int(episode), 1)}",
                params={"translation": translator_id},
                headers={"X-Requested-With": "XMLHttpRequest"},
            )
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError):
            return None
        html_fragment = ""
        if isinstance(payload, dict):
            html_fragment = str(payload.get("html") or "")
        elif isinstance(payload, str):
            html_fragment = payload
        match = _IFRAME_SRC_RE.search(html_fragment)
        if not match:
            return None
        src = html_mod.unescape(match.group(1)).strip()
        if src.startswith("//"):
            return f"https:{src}"
        return src

    async def _resolve_embed(
        self, embed_url: str, episode: int, translator_name: str
    ) -> list[DiscoveredWatchSource]:
        host = urlparse(embed_url).hostname or ""
        if "sibnet.ru" in host and self._sibnet_extractor is not None:
            try:
                items = await self._sibnet_extractor.extract_embed(embed_url, episode=episode)
            except ExternalServiceError:
                return []
            for item in items:
                item.translation_name = translator_name
            return items
        if self._aniboom_extractor is not None and "aniboom" in host:
            try:
                items = await self._aniboom_extractor.extract_embed(embed_url, episode=episode)
            except ExternalServiceError:
                return []
            for item in items:
                item.translation_name = translator_name
            return items
        return [
            DiscoveredWatchSource(
                episode=episode,
                translation_name=translator_name,
                translation_type="voice",
                provider_name=self.provider_name,
                source_name=f"animego-{host or 'embed'}",
                quality_label="Auto",
                source_type="embed",
                stream_url=embed_url,
            )
        ]

    async def _fetch(self, url: str, params: dict | None = None) -> str:
        try:
            response = await self.session.get(url, params=params)
            response.raise_for_status()
            return response.text
        except httpx.TimeoutException as exc:
            raise ExternalServiceTimeoutError(service_name=self.provider_name) from exc
        except httpx.HTTPError as exc:
            raise ExternalServiceUnavailableError(service_name=self.provider_name) from exc
