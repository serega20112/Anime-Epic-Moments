import re
from urllib.parse import urlparse

import httpx

from backend.config import Settings
from backend.domain.watch.value_object import DiscoveredWatchSource
from backend.infrastructure.external.watch_source_provider import WatchSourceProvider


class AniLibriaClient(WatchSourceProvider):
    """Ищет релизы AniLibria и извлекает HLS по эпизодам."""

    def __init__(
        self,
        api_url: str | None = None,
        provider_name: str | None = None,
    ):
        self.api_url = (api_url or Settings.anilibria_api_url).rstrip("/")
        self.provider_name = provider_name or "AniLibria"
        self.asset_origin = self._origin(self.api_url)
        self.session = httpx.AsyncClient(
            timeout=httpx.Timeout(6),
            trust_env=False,
            follow_redirects=True,
        )

    @staticmethod
    def _origin(url: str) -> str:
        """Возвращает схему и хост (origin) для построения относительных доменов."""
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}" if parsed.scheme and parsed.netloc else ""

    async def is_enabled(self) -> bool:
        return bool(self.api_url)

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
        if not await self.is_enabled():
            return []

        search_payload = await self._search_releases(title=title, limit=limit)
        if not search_payload:
            return []

        discovered: list[DiscoveredWatchSource] = []
        seen: set[tuple[str, str, str]] = set()
        for release in search_payload:
            if not await self._looks_relevant(
                release=release, requested_title=title, requested_year=year
            ):
                continue

            release_id = release.get("id")
            if not release_id:
                continue

            release_details = await self._get_release_details(release_id=int(release_id))
            if not release_details:
                continue

            episodes = release_details.get("episodes") or []
            if not isinstance(episodes, list):
                continue
            target_episode = next(
                (
                    item
                    for item in episodes
                    if isinstance(item, dict) and int(item.get("ordinal") or 0) == int(episode)
                ),
                None,
            )
            if not target_episode:
                continue

            translation_name = self.provider_name
            source_name = str(release.get("alias") or f"anilibria-{release_id}")
            for quality_label, field_name in (
                ("1080", "hls_1080"),
                ("720", "hls_720"),
                ("480", "hls_480"),
            ):
                stream_url = await self._normalize_link(target_episode.get(field_name))
                if not stream_url:
                    continue
                dedupe_key = (translation_name, quality_label, stream_url)
                if dedupe_key in seen:
                    continue
                seen.add(dedupe_key)
                discovered.append(
                    DiscoveredWatchSource(
                        episode=episode,
                        translation_name=translation_name,
                        translation_type="voice",
                        provider_name=self.provider_name,
                        source_name=source_name,
                        quality_label=quality_label,
                        stream_url=stream_url,
                    )
                )

        return discovered

    async def _search_releases(self, title: str, limit: int) -> list[dict]:
        try:
            response = await self.session.get(
                f"{self.api_url}/app/search/releases",
                params={"query": title, "limit": max(int(limit), 1)},
            )
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError, TypeError):
            return []
        return payload if isinstance(payload, list) else []

    async def _get_release_details(self, release_id: int) -> dict | None:
        try:
            response = await self.session.get(
                f"{self.api_url}/anime/releases/{release_id}",
                params={"include": "episodes"},
            )
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError, TypeError):
            return None
        return payload if isinstance(payload, dict) else None

    async def _looks_relevant(
        self, release: dict, requested_title: str, requested_year: int | None
    ) -> bool:
        release_year = release.get("year")
        if (
            requested_year
            and isinstance(release_year, int)
            and abs(release_year - requested_year) > 1
        ):
            return False

        requested = await self._normalize_title(requested_title)
        name = release.get("name") or {}
        candidates = [
            name.get("main"),
            name.get("english"),
            name.get("alternative"),
            release.get("alias"),
        ]
        for candidate in candidates:
            normalized_candidate = await self._normalize_title(candidate)
            if normalized_candidate and (
                requested in normalized_candidate or normalized_candidate in requested
            ):
                return True

        return requested_year is None

    async def _normalize_title(self, title: str | None) -> str:
        text = str(title or "").lower().strip()
        text = re.sub(r"[^a-zа-я0-9]+", " ", text, flags=re.IGNORECASE)
        return " ".join(text.split())

    async def _normalize_link(self, value: str | None) -> str | None:
        if not value:
            return None
        text = str(value).strip()
        if text.startswith("//"):
            return f"https:{text}"
        if text.startswith("/") and self.asset_origin:
            return f"{self.asset_origin}{text}"
        return text
