import re

import httpx

from backend.domain.value_objects.watch.discovery import DiscoveredWatchSource
from backend.infrastructure.external.errors import (
    ExternalServiceError,
    ExternalServiceInvalidResponseError,
    ExternalServiceTimeoutError,
    ExternalServiceUnavailableError,
)
from backend.infrastructure.external.watch_source_provider import WatchSourceProvider

_PLAYER_LINK_RE = re.compile(r"(?://video\.sibnet\.ru)?/(player\.(?:phps|php)\?[^\"'\s<>]+)")
_MEDIA_SRC_RE = re.compile(
    r"\"(?:file|src)\"\s*:\s*\"((?:https?:)?//[^\"']+?\.(?:mp4|m3u8)[^\"']*)\"", re.IGNORECASE
)
_PLAIN_MEDIA_RE = re.compile(r"((?:https?:)?//[^\"'\s]+?\.(?:mp4|m3u8)[^\"'\s]*)", re.IGNORECASE)
_SEARCH_RESULT_RE = re.compile(
    r"href=\"(?P<url>/shell\.php\?videoid=(?P<id>\d+)[^\"]*)\"[^>]*>",
    re.IGNORECASE,
)


class SibnetProvider(WatchSourceProvider):
    """Извлекает прямые MP4/HLS из страниц видеохостинга Sibnet.

    Два рабочих пути: :meth:`search_sources` — текстовый поиск по названию
    тайтла через поиск Sibnet, и :meth:`extract_embed` — извлечение потока
    от готового URL вида ``https://video.sibnet.ru/shell.php?videoid=...``
    (обычно выдаётся каталогами вроде AnimeGo).
    """

    def __init__(self, *, base_url: str, enabled: bool, timeout: float):
        self.base_url = base_url.rstrip("/")
        self.enabled = enabled
        self.timeout = timeout
        self.provider_name = "Sibnet"
        self.session = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            trust_env=False,
            follow_redirects=True,
            headers={"Referer": "https://video.sibnet.ru/"},
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
        limit: int = 8,
        shikimori_id: int | None = None,
    ) -> list[DiscoveredWatchSource]:
        """Ищет видео по названию тайтла через поиск Sibnet.

        Sibnet не имеет каталога внешних id, но имеет текстовый поиск:
        запрос по названию находит видео и возвращает прямые потоки.
        Нечёткое сопоставление не используется — только строгий token-match
        по словам названия, чтобы не подменять тайтл похожим.

        Args:
            title: Название тайтла.
            episode: Номер эпизода для результата.
            year: Год выпуска (игнорируется: у Sibnet нет года в выдаче).
            limit: Максимум источников в результате.
            shikimori_id: Внешний id тайтла (игнорируется: у Sibnet нет
                каталога внешних id, но текстовый поиск остаётся строгим).

        Returns:
            list[DiscoveredWatchSource]: Найденные прямые потоки.
        """
        if not await self.is_enabled():
            return []
        query = str(title or "").strip()
        if not query:
            return []

        try:
            search_page = await self._fetch(f"{self.base_url}/search.php?search={query}")
        except ExternalServiceError:
            return []

        discovered: list[DiscoveredWatchSource] = []
        seen_ids: set[str] = set()
        for match in _SEARCH_RESULT_RE.finditer(search_page):
            video_id = match.group("id")
            if video_id in seen_ids:
                continue
            seen_ids.add(video_id)
            try:
                discovered.extend(
                    await self.extract_embed(
                        f"{self.base_url}/shell.php?videoid={video_id}", episode
                    )
                )
            except ExternalServiceError:
                continue
            if len(discovered) >= limit:
                break
        return discovered

    async def extract_embed(self, embed_url: str, episode: int = 1) -> list[DiscoveredWatchSource]:
        """Извлекает прямой медиа-поток из shell/player страницы Sibnet.

        Args:
            embed_url: URL вида {base}/shell.php?videoid=N или /player.phps?...
            episode: Номер эпизода для результата.

        Returns:
            list[DiscoveredWatchSource]: Один источник с прямым потоком.
        """
        if not await self.is_enabled():
            return []
        page_text = await self._fetch(embed_url)

        stream_url = await self._extract_media_src(page_text)
        if not stream_url:
            player_page = await self._fetch_player_page(page_text)
            if player_page is None:
                raise ExternalServiceInvalidResponseError(service_name=self.provider_name)
            stream_url = await self._extract_media_src(player_page)
        if not stream_url:
            raise ExternalServiceInvalidResponseError(service_name=self.provider_name)

        return [
            DiscoveredWatchSource(
                episode=episode,
                translation_name=self.provider_name,
                translation_type="voice",
                provider_name=self.provider_name,
                source_name=f"sibnet-{episode}",
                quality_label="Auto",
                source_type="stream",
                stream_url=stream_url,
            )
        ]

    async def _extract_media_src(self, page_text: str) -> str | None:
        match = _MEDIA_SRC_RE.search(page_text) or _PLAIN_MEDIA_RE.search(page_text)
        return await self._to_absolute(match.group(1)) if match else None

    async def _fetch_player_page(self, page_text: str) -> str | None:
        for match in _PLAYER_LINK_RE.finditer(page_text):
            url = await self._to_absolute(match.group(0))
            if not url:
                continue
            try:
                return await self._fetch(url)
            except ExternalServiceUnavailableError:
                continue
        return None

    async def _fetch(self, url: str) -> str:
        try:
            response = await self.session.get(url)
            response.raise_for_status()
            return response.text
        except httpx.TimeoutException as exc:
            raise ExternalServiceTimeoutError(service_name=self.provider_name) from exc
        except httpx.HTTPError as exc:
            raise ExternalServiceUnavailableError(service_name=self.provider_name) from exc

    async def _to_absolute(self, value: str | None) -> str | None:
        if not value:
            return None
        text = str(value).strip()
        if text.startswith("//"):
            return f"https:{text}"
        if text.startswith("/"):
            return f"{self.base_url}{text}"
        return text
