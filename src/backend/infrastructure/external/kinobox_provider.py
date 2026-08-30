import re

import httpx

from backend.domain.value_objects.watch.discovery import DiscoveredWatchSource
from backend.infrastructure.external.errors import (
    ExternalServiceInvalidResponseError,
    ExternalServiceTimeoutError,
    ExternalServiceUnavailableError,
)
from backend.infrastructure.external.http_guard import read_json_limited
from backend.infrastructure.external.watch_source_provider import WatchSourceProvider

_KINOBOX_SOURCE_LABELS = {
    "kodik": "Kodik",
    "alloha": "Alloha",
    "collaps": "Collaps",
    "rezka": "HDRezka",
    "videocdn": "VideoCDN",
    "hdvb": "HDVB",
    "ustore": "Ustore",
}


class KinoboxProvider(WatchSourceProvider):
    """Отдаёт embed-источники агрегатора Kinobox через его JSON API.

    Вместо kinobox.min.js (собственный UI, промо-пункты меню) используется
    открытый эндпоинт ``/api/players``: он возвращает список плееров
    балансеров (Kodik, Alloha, Collaps, Rezka и др.) по тайтлу. Каждый плеер
    превращается в embed-источник и показывается в собственном UI проекта —
    выбор озвучки/источника остаётся на нашей стороне.

    Внутри сторонних iframe-плееров возможна реклама балансеров: она
    не относится к проекту, о чём пользователя предупреждает дисклеймер
    на странице просмотра.
    """

    def __init__(self, *, base_url: str, enabled: bool, timeout: float):
        self.base_url = base_url.rstrip("/")
        self.enabled = enabled
        self.timeout = timeout
        self.provider_name = "Kinobox"
        self.session = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            trust_env=False,
            follow_redirects=True,
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
        """Ищет плееры тайтла через Kinobox API.

        Args:
            title: Название аниме для поиска.
            episode: Номер эпизода (embed-плеер содержит все серии).
            year: Год релиза (Kinobox не использует).
            limit: Максимум обрабатываемых плееров.
            shikimori_id: Внешний id тайтла (игнорируется: у Kinobox свой id).

        Returns:
            list[DiscoveredWatchSource]: Embed-источники по одному на плеер.
        """
        if not await self.is_enabled():
            return []

        players = await self._request_players(title=title)
        discovered: list[DiscoveredWatchSource] = []
        seen: set[str] = set()
        for player in players[: max(int(limit), 1)]:
            if not isinstance(player, dict):
                continue
            raw_iframe = str(player.get("iframeUrl") or "").strip()
            iframe_url = await self._ensure_https(raw_iframe)
            if not iframe_url.startswith("https://") or raw_iframe in seen:
                continue
            seen.add(raw_iframe)

            source_key = str(player.get("source") or "").strip().lower()
            source_label = _KINOBOX_SOURCE_LABELS.get(source_key, source_key or "Kinobox")
            translation_title = str((player.get("translation") or {}).get("title") or "").strip()
            translation_name = translation_title or source_label
            quality_label = str(player.get("quality") or "").strip() or "Auto"

            discovered.append(
                DiscoveredWatchSource(
                    episode=episode,
                    translation_name=translation_name,
                    translation_type="voice",
                    provider_name=self.provider_name,
                    source_name=f"kinobox-{source_key or 'player'}",
                    quality_label=quality_label,
                    source_type="embed",
                    stream_url=await self._ensure_https(iframe_url),
                )
            )
        return discovered

    async def _request_players(self, title: str) -> list:
        try:
            response = await self.session.get(
                f"{self.base_url}/api/players",
                params={"title": title},
            )
            response.raise_for_status()
            payload = read_json_limited(response, service_name=self.provider_name)
        except httpx.TimeoutException as exc:
            raise ExternalServiceTimeoutError(service_name=self.provider_name) from exc
        except httpx.HTTPError as exc:
            raise ExternalServiceUnavailableError(service_name=self.provider_name) from exc
        except ValueError as exc:
            raise ExternalServiceInvalidResponseError(service_name=self.provider_name) from exc
        if not isinstance(payload, list):
            raise ExternalServiceInvalidResponseError(service_name=self.provider_name)
        return payload

    @staticmethod
    async def _ensure_https(url: str) -> str:
        text = str(url).strip()
        if text.startswith("//"):
            return f"https:{text}"
        return re.sub(r"^http://", "https://", text)
