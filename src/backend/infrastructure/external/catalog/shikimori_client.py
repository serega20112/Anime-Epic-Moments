"""Клиент Shikimori для русских названий и описаний аниме.

Shikimori повторяет базу MyAnimeList, поэтому MAL-идентификатор из
``external_id`` совпадает с ключом Shikimori и поиск идёт по нему, без
нечёткого сравнения названий. Русские метаданные запрашиваются пачкой
по списку идентификаторов и кэшируются в общем хранилище. Любой сбой
сети или разбора означает «русских данных нет» и не блокирует запрос.
"""

from __future__ import annotations

import logging
from collections.abc import Iterable

import httpx

from backend.config import Settings
from backend.infrastructure.cache.key_value_store import KeyValueStore
from backend.infrastructure.external._common import ExternalServiceError, read_json_limited

SHIKIMORI_TITLES_ENDPOINT = "/animes"
MAX_BATCH_SIZE = 20
RU_TITLE_TTL_SECONDS = 60 * 60 * 24 * 30
RU_TITLE_TEMPLATE = "ru_title:{id}"
RU_DESC_TEMPLATE = "ru_desc:{id}"
_MAX_MISS = object()

logger = logging.getLogger("anime_epic_moments")


class ShikimoriClient:
    """Загружает русские названия и описания по MAL-идентификатору."""

    provider_name = "Shikimori"

    def __init__(
        self,
        session: httpx.AsyncClient,
        store: KeyValueStore | None = None,
        base_url: str | None = None,
    ) -> None:
        """Создать клиент Shikimori."""
        self.session = session
        self.store = store
        self.base_url = (base_url or Settings.shikimori_api_url).rstrip("/")
        self.enabled = Settings.shikimori_enabled
        self.headers = {"User-Agent": Settings.shikimori_user_agent}
        if Settings.shikimori_token:
            self.headers["Authorization"] = f"Bearer {Settings.shikimori_token}"

    async def is_enabled(self) -> bool:
        """Сообщить, доступно ли обогащение русскими названиями."""
        return self.enabled

    async def fetch_russian(
        self,
        mal_ids: Iterable[int | str],
    ) -> dict[int, tuple[str | None, str | None]]:
        """Загрузить русские названия и описания для пачки MAL-идентификаторов.

        Из Shikimori запрашиваются только идентификаторы без закэшированного
        русского названия, одним пакетным запросом.
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
        """Запросить одну пачку у Shikimori и заполнить итоговое отображение."""
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
        """Прочитать закэшированную пару «название и описание»."""
        if self.store is None:
            return (_MAX_MISS, _MAX_MISS)
        try:
            title = await self.store.get(RU_TITLE_TEMPLATE.format(id=mal_id), default=_MAX_MISS)
            description = await self.store.get(
                RU_DESC_TEMPLATE.format(id=mal_id), default=_MAX_MISS
            )
        except Exception as error:
            logger.debug("shikimori cache read failed reason=%s", error.__class__.__name__)
            return (_MAX_MISS, _MAX_MISS)
        if title is _MAX_MISS or description is _MAX_MISS:
            return (_MAX_MISS, _MAX_MISS)
        return (title, description)

    async def _cache(self, mal_id: int, title: str | None, description: str | None) -> None:
        """Сохранить пару «название и описание» в кэш."""
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
        except Exception as error:
            logger.debug("shikimori cache write failed reason=%s", error.__class__.__name__)

    @staticmethod
    def _parse_id(value) -> int | None:
        """Разобрать числовой идентификатор из сырого значения."""
        try:
            numeric = int(value)
        except (TypeError, ValueError):
            return None
        return numeric if numeric > 0 else None

    @staticmethod
    def _clean(value) -> str:
        """Обрезать пробелы в строковом значении."""
        text = str(value or "").strip()
        return text if text and text.lower() != "null" else ""
