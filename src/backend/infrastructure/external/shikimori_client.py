"""Shikimori client for Russian anime titles and descriptions.

Shikimori is the Russian anime database, a mirror of MyAnimeList (MAL) that
carries its own ``russian`` name and a Russian ``description`` for a large part
of the catalog. Because Shikimori mirrors MAL, the numeric MAL id we already
have as ``external_id`` (via Jikan's ``mal_id`` and AniList's ``idMal``) is the
same key Shikimori indexes by, so we match by id — no fuzzy name matching.

This client is an enrichment layer over the Jikan/AniList results inside
:class:`AnimeApiClient`. It fetches Russian metadata in batches by MAL id
(``GET /animes?ids=1,2,3``) so a catalog page of 20 tiles costs a single
upstream request instead of N+1, and caches each id's RU title/description in
the shared key-value store. Integration is best-effort: any network or parsing
failure degrades to "no Russian data" and never blocks a request.
"""

from __future__ import annotations

from collections.abc import Iterable

import httpx

from backend.config import Settings
from backend.infrastructure.cache.key_value_store import KeyValueStore
from backend.infrastructure.external.errors import ExternalServiceError
from backend.infrastructure.external.http_guard import read_json_limited

SHIKIMORI_TITLES_ENDPOINT = "/animes"
MAX_BATCH_SIZE = 20
RU_TITLE_TTL_SECONDS = 60 * 60 * 24 * 30  # 30 days
RU_TITLE_TEMPLATE = "ru_title:{id}"
RU_DESC_TEMPLATE = "ru_desc:{id}"
_MAX_MISS = object()


class ShikimoriClient:
    """Fetch Russian titles/descriptions by MAL id through the Shikimori REST API."""

    provider_name = "Shikimori"

    def __init__(
        self,
        session: httpx.AsyncClient,
        store: KeyValueStore | None = None,
        base_url: str | None = None,
    ) -> None:
        """Initialize the client.

        Args:
            session: Shared HTTP session owned by the orchestrating facade.
            store: Optional cache store for RU title/description values.
            base_url: Shikimori API base URL (defaults to settings).
        """
        self.session = session
        self.store = store
        self.base_url = (base_url or Settings.shikimori_api_url).rstrip("/")
        self.enabled = Settings.shikimori_enabled
        self.headers = {"User-Agent": Settings.shikimori_user_agent}
        if Settings.shikimori_token:
            self.headers["Authorization"] = f"Bearer {Settings.shikimori_token}"

    async def is_enabled(self) -> bool:
        """Return whether Russian-title enrichment is available.

        Returns:
            bool: True when the Shikimori source is enabled.
        """
        return self.enabled

    async def fetch_russian(
        self,
        mal_ids: Iterable[int | str],
    ) -> dict[int, tuple[str | None, str | None]]:
        """Fetch Russian titles/descriptions for a batch of MAL ids.

        Only ids without a cached RU title are requested from Shikimori, in a
        single batched HTTP call. Fresh cache hits are returned immediately.

        Args:
            mal_ids: Collection of MAL anime ids.

        Returns:
            dict[int, tuple[str | None, str | None]]: Mapping of mal_id to a
                ``(russian_title, russian_description)`` pair (both may be None
                when Shikimori does not know the title).
        """
        ids = sorted({int(i) for i in mal_ids if str(i or "").strip()})
        if not ids or not self.enabled:
            return {}
        result: dict[int, tuple[str | None, str | None]] = {}
        miss_ids: list[int] = []
        for mal_id in ids:
            title, description = await self._get_cached(mal_id)
            if title is _MAX_MISS:
                miss_ids.append(mal_id)
            else:
                result[mal_id] = (title, description)

        if not miss_ids:
            return result

        for chunk_start in range(0, len(miss_ids), MAX_BATCH_SIZE):
            chunk = miss_ids[chunk_start : chunk_start + MAX_BATCH_SIZE]
            await self._fill_batch(chunk, result)

        return result

    async def _fill_batch(
        self,
        chunk: list[int],
        result: dict[int, tuple[str | None, str | None]],
    ) -> None:
        """Request one chunk from Shikimori and populate the result map.

        Args:
            chunk: MAL ids to fetch in this batch.
            result: Result mapping to fill in-place.
        """
        params = {"ids": ",".join(str(i) for i in chunk), "limit": MAX_BATCH_SIZE}
        try:
            response = await self.session.get(
                f"{self.base_url}{SHIKIMORI_TITLES_ENDPOINT}",
                params=params,
                headers=self.headers,
            )
            response.raise_for_status()
            payload = read_json_limited(response, service_name=self.provider_name)
        except (httpx.HTTPError, ValueError, TypeError, ExternalServiceError):
            return
        if not isinstance(payload, list):
            return

        by_id: dict[int, dict] = {}
        for entry in payload:
            if not isinstance(entry, dict):
                continue
            mal_id = self._parse_id(entry.get("id"))
            if mal_id is not None:
                by_id[mal_id] = entry

        for mal_id in chunk:
            entry = by_id.get(mal_id)
            if entry is None:
                result[mal_id] = (None, None)
                await self._cache(mal_id, None, None)
                continue
            russian = self._clean(entry.get("russian"))
            description = self._clean(entry.get("description"))
            result[mal_id] = (russian or None, description or None)
            await self._cache(mal_id, russian or None, description or None)

    async def _get_cached(self, mal_id: int) -> tuple:
        """Read a cached RU title/description pair.

        Args:
            mal_id: MAL anime id.

        Returns:
            tuple: ``(title, description)`` when cached, else a miss sentinel.
        """
        if self.store is None:
            return (_MAX_MISS, _MAX_MISS)
        try:
            title = await self.store.get(RU_TITLE_TEMPLATE.format(id=mal_id), default=_MAX_MISS)
            description = await self.store.get(
                RU_DESC_TEMPLATE.format(id=mal_id), default=_MAX_MISS
            )
        except Exception:
            return (_MAX_MISS, _MAX_MISS)
        if title is _MAX_MISS or description is _MAX_MISS:
            return (_MAX_MISS, _MAX_MISS)
        return (title, description)

    async def _cache(self, mal_id: int, title: str | None, description: str | None) -> None:
        """Store a RU title/description pair in the cache store.

        Args:
            mal_id: MAL anime id.
            title: RU title or None.
            description: RU description or None.
        """
        if self.store is None:
            return
        try:
            await self.store.set(
                RU_TITLE_TEMPLATE.format(id=mal_id),
                title,
                ttl_seconds=RU_TITLE_TTL_SECONDS,
            )
            await self.store.set(
                RU_DESC_TEMPLATE.format(id=mal_id),
                description,
                ttl_seconds=RU_TITLE_TTL_SECONDS,
            )
        except Exception:
            pass

    @staticmethod
    def _parse_id(value) -> int | None:
        """Parse a numeric id from a raw value.

        Args:
            value: Raw id value.

        Returns:
            int | None: Parsed id or None.
        """
        try:
            numeric = int(value)
        except (TypeError, ValueError):
            return None
        return numeric if numeric > 0 else None

    @staticmethod
    def _clean(value) -> str:
        """Trim a raw string value.

        Args:
            value: Raw value.

        Returns:
            str: Cleaned value or empty string.
        """
        text = str(value or "").strip()
        return text if text and text.lower() != "null" else ""
