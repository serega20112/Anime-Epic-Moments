"""Eporner API watch source provider (hentai/adult тайтлы).

Официальный публичный JSON API (без капчи и куки):
* поиск — ``GET /api/v2/video/search/?query=...&format=json``;
* потоки — страница видео содержит ``hash``, по которому ручка
  ``GET /xhr/video/{id}?hash=...`` возвращает подписанные прямые MP4/HLS
  (алгоритм вычисления hash восстановлен из ``vjs.js``, см. yt-dlp).

Провайдер нужен для hentai-тайтлов, где hanime недоступен по сети/региону.
"""

from __future__ import annotations

import re

import httpx

from backend.domain.value_objects.watch.discovery import DiscoveredWatchSource
from backend.infrastructure.external.errors import (
    ExternalServiceError,
    ExternalServiceTimeoutError,
    ExternalServiceUnavailableError,
)
from backend.infrastructure.external.watch_source_provider import WatchSourceProvider

_WORD_RE = re.compile(r"[a-z0-9а-яё]+", re.IGNORECASE)
_HASH_RE = re.compile(r'hash\s*[:=]\s*["\']([\da-f]{32})', re.IGNORECASE)
_VIDEO_ID_RE = re.compile(r"^[a-zA-Z0-9]+$")
_BASE36_DIGITS = "0123456789abcdefghijklmnopqrstuvwxyz"
_MAX_EXTRA_WORDS = 3
_MAX_STREAMS_PER_VIDEO = 3

_BROWSER_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)


def _to_base36(number: int) -> str:
    """Переводит число в строку base36 (как в encode_base_n yt-dlp)."""
    if number <= 0:
        return "0"
    result = ""
    while number:
        number, remainder = divmod(number, 36)
        result = _BASE36_DIGITS[remainder] + result
    return result


def _calc_hash(page_hash: str) -> str:
    """Вычисляет param ``hash`` для xhr/video по 32-байтному hex из страницы.

    Каждые 8 hex-цифр трактуются как int(base 16) и переводятся в base36.

    Args:
        page_hash: 32 hex-символа ``hash`` со страницы видео.

    Returns:
        str: Строка из четырёх base36-чанков.
    """
    return "".join(
        _to_base36(int(page_hash[offset : offset + 8], 16)) for offset in range(0, 32, 8)
    )


class EpornerProvider(WatchSourceProvider):
    """Ищет прямые MP4-потоки на Eporner через публичный JSON API.

    Транспортные сбои транслируются в
    :mod:`backend.infrastructure.external.errors`; неожиданная форма ответа
    деградирует в пустой результат. Кандидаты фильтруются строгим
    token-match по названию, чтобы не подменять тайтл похожим видео.
    """

    def __init__(self, *, base_url: str, enabled: bool, timeout: float):
        self.base_url = base_url.rstrip("/")
        self.enabled = enabled
        self.timeout = timeout
        self.provider_name = "Eporner"
        self.session = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            # trust_env выключен у остальных провайдеров, но Eporner из-за
            # региональных ограничений требует проброса доверенного окружения
            # (маршрут/прокси) — иначе стабильный ConnectError.
            trust_env=True,
            follow_redirects=True,
            headers={
                "User-Agent": _BROWSER_UA,
                "Accept-Language": "en-US,en;q=0.9",
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
        limit: int = 8,
        shikimori_id: int | None = None,
    ) -> list[DiscoveredWatchSource]:
        """Ищет прямые MP4 по названию через поиск Eporner.

        Args:
            title: Название тайтла.
            episode: Номер эпизода для результата.
            year: Год выпуска (игнорируется: у Eporner нет года в выдаче).
            limit: Максимум кандидатов на выбор из поиска.
            shikimori_id: Внешний id (игнорируется: у Eporner свой id,
                текстовая адресация остаётся строгой по токенам).

        Returns:
            list[DiscoveredWatchSource]: Найденные прямые MP4-источники.
        """
        if not await self.is_enabled():
            return []

        query = str(title or "").strip()
        if not query:
            return []
        try:
            payload = await self._search_page(query, per_page=max(int(limit), 1))
        except ExternalServiceError:
            return []
        videos = payload.get("videos") if isinstance(payload, dict) else None
        if not isinstance(videos, list):
            return []

        discovered: list[DiscoveredWatchSource] = []
        seen_urls: set[str] = set()
        for video in videos:
            if not isinstance(video, dict) or not await self._is_relevant(query, video):
                continue
            video_id = str(video.get("id") or "").strip()
            if not _VIDEO_ID_RE.match(video_id):
                continue
            try:
                streams = await self._video_streams(video_id)
            except ExternalServiceError:
                continue
            for quality_label, stream_url in streams:
                if stream_url in seen_urls:
                    continue
                seen_urls.add(stream_url)
                discovered.append(
                    DiscoveredWatchSource(
                        episode=int(episode),
                        translation_name=self.provider_name,
                        translation_type="voice",
                        language="ja",
                        provider_name=self.provider_name,
                        source_name=f"eporner-{video_id}",
                        quality_label=quality_label,
                        stream_url=stream_url,
                    )
                )
        return discovered

    async def _search_page(self, query: str, per_page: int) -> dict:
        """Возвращает страницу поиска Eporner в виде JSON.

        Args:
            query: Поисковый запрос (название тайтла).
            per_page: Сколько видео запросить.

        Returns:
            dict: Тело ответа поиска.

        Raises:
            ExternalServiceTimeoutError: Таймаут запроса.
            ExternalServiceUnavailableError: Сеть/HTTP-ошибка.
        """
        response = await self._get(
            f"{self.base_url}/api/v2/video/search/",
            params={
                "query": query,
                "per_page": str(per_page),
                "page": "1",
                "thumbsize": "medium",
                "format": "json",
            },
        )
        try:
            payload = response.json()
        except ValueError:
            return {}
        return payload if isinstance(payload, dict) else {}

    async def _video_streams(self, video_id: str) -> list[tuple[str, str]]:
        """Возвращает (качество, поток) для видео Eporner по id.

        Args:
            video_id: Идентификатор видео.

        Returns:
            list[tuple[str, str]]: Пары (quality_label, stream_url).

        Raises:
            ExternalServiceTimeoutError: Таймаут запроса.
            ExternalServiceUnavailableError: Сеть/HTTP-ошибка.
        """
        page_text = await self._get_text(f"{self.base_url}/video-{video_id}/")
        hash_match = _HASH_RE.search(page_text)
        if not hash_match:
            return []
        payload = await self._get_json(
            f"{self.base_url}/xhr/video/{video_id}",
            params={
                "hash": _calc_hash(hash_match.group(1)),
                "device": "generic",
                "domain": self.base_url.replace("https://", "").replace("http://", "").rstrip("/"),
                "fallback": "false",
            },
        )
        sources = payload.get("sources") if isinstance(payload, dict) else None
        if not isinstance(sources, dict):
            return []

        streams: list[tuple[str, str]] = []
        for kind in ("mp4", "hls"):
            formats = sources.get(kind) if kind in sources else None
            if not isinstance(formats, dict):
                continue
            candidates: list[tuple[int, str, str]] = []
            for label, entry in formats.items():
                if not isinstance(entry, dict):
                    continue
                src = str(entry.get("src") or "").strip()
                if not src.startswith("http"):
                    continue
                label_text = str(entry.get("labelShort") or label or src)
                quality = self._quality_digits(label_text)
                candidates.append((quality, label_text, src))
            candidates.sort(key=lambda triple: triple[0], reverse=True)
            for _quality, label_text, src in candidates[:_MAX_STREAMS_PER_VIDEO]:
                streams.append((label_text, src))
            if streams:
                break
        return streams

    @staticmethod
    def _quality_digits(value: str) -> int:
        digits = "".join(character for character in str(value) if character.isdigit())
        return int(digits) if digits else 0

    async def _is_relevant(self, title: str, item: dict) -> bool:
        """Проверяет совпадение названия по токенам (как в Hanime/Kodik).

        Args:
            title: Запрошенное название.
            item: Элемент выдачи поиска.

        Returns:
            bool: True когда все слова запроса есть в названии и лишних
            слов немного.
        """
        query_tokens = set(_WORD_RE.findall(title.lower()))
        if not query_tokens:
            return False
        candidates = (item.get("title"), item.get("keywords"))
        for candidate in candidates:
            name_tokens = set(_WORD_RE.findall(str(candidate or "").lower()))
            if not name_tokens:
                continue
            missing = query_tokens - name_tokens
            extra = name_tokens - query_tokens
            if not missing and len(extra) <= _MAX_EXTRA_WORDS:
                return True
        return False

    async def _get(self, url: str, *, params: dict[str, str] | None = None) -> httpx.Response:
        """GET-запрос с трансляцией транспортных ошибок.

        Args:
            url: Абсолютный URL.
            params: Query-параметры.

        Returns:
            httpx.Response: Ответ сервиса.

        Raises:
            ExternalServiceTimeoutError: Таймаут запроса.
            ExternalServiceUnavailableError: Сеть/HTTP-ошибка.
        """
        try:
            response = await self.session.get(url, params=params)
            response.raise_for_status()
            return response
        except httpx.TimeoutException as exc:
            raise ExternalServiceTimeoutError(service_name=self.provider_name) from exc
        except httpx.HTTPError as exc:
            raise ExternalServiceUnavailableError(service_name=self.provider_name) from exc

    async def _get_text(self, url: str) -> str:
        response = await self._get(url)
        return response.text

    async def _get_json(self, url: str, *, params: dict[str, str]) -> dict:
        response = await self._get(url, params=params)
        try:
            payload = response.json()
        except ValueError:
            return {}
        return payload if isinstance(payload, dict) else {}
