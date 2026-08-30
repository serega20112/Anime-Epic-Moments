"""Hanime.tv API watch source provider.

Транспорт построен на ``curl_cffi`` с браузерным TLS-отпечатком (сайт за
Cloudflare, который отсекает python-httpx по отпечатку), с DoH-фолбэком на
случай отравленного/недоступного локального DNS и опциональным прокси для
сетей, где тайтл заблокирован целиком.
"""

from __future__ import annotations

import logging
import re

from curl_cffi.curl import CurlOpt
from curl_cffi.requests import AsyncSession
from curl_cffi.requests.exceptions import DNSError, RequestException
from curl_cffi.requests.exceptions import Timeout as CurlTimeout

from backend.domain.value_objects.watch.discovery import DiscoveredWatchSource
from backend.infrastructure.external.errors import (
    ExternalServiceTimeoutError,
    ExternalServiceUnavailableError,
)
from backend.infrastructure.external.watch_source_provider import WatchSourceProvider

logger = logging.getLogger(__name__)

_WORD_RE = re.compile(r"[a-z0-9а-яё]+")
_QUALITY_IN_URL_RE = re.compile(r"(?:^|[^\d])(360|480|540|720|1080|1440|2160)(?:p|[^\d]|$)")
_DOH_RESOLVER_URL = "https://cloudflare-dns.com/dns-query"


class HanimeProvider(WatchSourceProvider):
    """Ищет оригинальные HLS-потоки на Hanime.tv через публичный JSON API v8.

    Провайдер получает готовую конфигурацию через DI и не читает окружение
    напрямую. Транспортные сбои транслируются в
    :mod:`backend.infrastructure.external.errors`, а неожиданные формы ответа
    деградируют в пустой результат.
    """

    def __init__(
        self,
        *,
        base_url: str,
        enabled: bool,
        timeout: float,
        proxy: str = "",
        cf_clearance: str = "",
        user_agent: str = "",
    ):
        self.base_url = base_url.rstrip("/")
        self.enabled = enabled
        self.timeout = timeout
        self.provider_name = "Hanime"
        self.proxy = str(proxy or "").strip()
        self._session_kwargs: dict = {
            "impersonate": "chrome",
            "timeout": timeout,
        }
        if self.proxy:
            self._session_kwargs["proxy"] = self.proxy
        clearance = str(cf_clearance or "").strip()
        if clearance:
            self._session_kwargs["headers"] = {
                "Cookie": f"cf_clearance={clearance}",
                "User-Agent": str(user_agent or "").strip(),
            }
        self.session: AsyncSession = AsyncSession(**dict(self._session_kwargs))
        self._resolve_session: AsyncSession | None = None

    async def aclose(self) -> None:
        """Close the underlying HTTP clients."""
        await self.session.close()
        if self._resolve_session is not None:
            await self._resolve_session.close()
            self._resolve_session = None

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
        """Поиск по тайтлу через поиск Hanime и детальную ручку видео.

        Args:
            title: Название тайтла.
            episode: Номер эпизода для результата.
            year: Год выпуска для смягчённой сверки (±1).
            limit: Максимум источников в результате.
            shikimori_id: Внешний id тайтла (игнорируется: у Hanime свой id).

        Returns:
            list[DiscoveredWatchSource]: Найденные HLS-источники.
        """
        candidates = await self._search_videos(title, year=year)

        discovered: list[DiscoveredWatchSource] = []
        seen_urls: set[str] = set()
        for video in candidates[:limit]:
            stream_urls = await self._video_streams(video.get("id"))
            quality = await self._quality_label(stream_urls)
            for stream_url in stream_urls:
                if stream_url in seen_urls:
                    continue
                seen_urls.add(stream_url)
                discovered.append(
                    DiscoveredWatchSource(
                        episode=episode,
                        translation_name=self.provider_name,
                        translation_type="voice",
                        language="ja",
                        provider_name=self.provider_name,
                        source_name=f"hanime-{video.get('id') or ''}".rstrip("-"),
                        quality_label=quality,
                        stream_url=stream_url,
                    )
                )
        return discovered

    async def _search_videos(self, title: str, *, year: int | None = None) -> list[dict]:
        """Ищет видео на Hanime и фильтрует кандидатов по названию и году.

        Args:
            title: Название тайтла.
            year: Год выпуска или None.

        Returns:
            list[dict]: Релевантные элементы поиска (id, name и т.д.).
        """
        payload = await self._post_json(
            "/api/v8/search",
            json_body={
                "search_text": title,
                "tags": [],
                "tags_mode": "AND",
                "order_by": "created_at",
                "ordering": "desc",
                "offset": 0,
            },
        )
        if not isinstance(payload, dict):
            return []
        raw_items: list[dict] = []
        for key in ("hentai_videos", "videos"):
            value = payload.get(key)
            if isinstance(value, list):
                raw_items.extend(item for item in value if isinstance(item, dict))

        relevant: list[dict] = []
        for item in raw_items:
            if not await self._is_relevant(title, item):
                continue
            if year is not None and not await self._matches_year(year, item):
                continue
            relevant.append(item)
        return relevant

    async def _video_streams(self, video_id: object) -> list[str]:
        """Забирает HLS-ссылки конкретного видео.

        Args:
            video_id: Идентификатор видео на Hanime.

        Returns:
            list[str]: Список потоковых URL (может быть пустым).
        """
        normalized_id = str(video_id or "").strip()
        if not normalized_id:
            return []
        payload = await self._get_json("/api/v8/video", params={"id": normalized_id})
        if not isinstance(payload, dict):
            return []
        streams = payload.get("video_streams_url")
        if isinstance(streams, str):
            streams = [streams]
        if not isinstance(streams, list):
            return []
        urls: list[str] = []
        for stream in streams:
            url = str(stream or "").strip()
            if url.startswith("http"):
                urls.append(url)
        return urls

    async def _is_relevant(self, title: str, item: dict) -> bool:
        """Проверяет совпадение названия по токенам (как в Kodik-клиенте).

        Args:
            title: Запрошенное название.
            item: Элемент выдачи поиска.

        Returns:
            bool: True когда все слова запроса есть в имени и лишних слов немного.
        """
        query_tokens = set(_WORD_RE.findall(title.lower()))
        if not query_tokens:
            return False
        names = (
            str(item.get("name") or ""),
            str(item.get("original_title") or ""),
            str(item.get("english_title") or ""),
        )
        for name in names:
            name_tokens = set(_WORD_RE.findall(name.lower()))
            if not name_tokens:
                continue
            missing = query_tokens - name_tokens
            extra = name_tokens - query_tokens
            if not missing and len(extra) <= 3:
                return True
        return False

    @staticmethod
    async def _matches_year(expected_year: int, item: dict) -> bool:
        """Сверяет год выпуска с допуском ±1 год.

        Args:
            expected_year: Ожидаемый год выпуска.
            item: Элемент выдачи поиска.

        Returns:
            bool: True когда год неизвестен либо близок к ожидаемому.
        """
        released_at = str(item.get("released_at") or "")
        match = re.search(r"(\d{4})", released_at)
        if not match:
            return True
        try:
            actual_year = int(match.group(1))
        except ValueError:
            return True
        return abs(actual_year - expected_year) <= 1

    @staticmethod
    async def _quality_label(stream_urls: list[str]) -> str:
        """Определяет метку качества по URL потока.

        Args:
            stream_urls: Список потоковых URL.

        Returns:
            str: Высота разрешения цифрами или «720» по умолчанию.
        """
        for stream_url in stream_urls:
            match = _QUALITY_IN_URL_RE.search(stream_url.lower())
            if match:
                return match.group(1)
        return "720"

    async def _post_json(self, path: str, *, json_body: dict) -> object:
        """POST-запрос к Hanime API с разбором JSON.

        Args:
            path: Путь относительно base_url.
            json_body: Тело запроса.

        Returns:
            object: Разобранный JSON или None при ошибке.
        """
        return await self._request_json("POST", path, json_body=json_body)

    async def _get_json(self, path: str, *, params: dict | None = None) -> object:
        """GET-запрос к Hanime API с разбором JSON.

        Args:
            path: Путь относительно base_url.
            params: Query-параметры.

        Returns:
            object: Разобранный JSON или None при ошибке.
        """
        return await self._request_json("GET", path, params=params)

    async def _request_json(
        self,
        method: str,
        path: str,
        *,
        json_body: dict | None = None,
        params: dict | None = None,
    ) -> object:
        """Выполняет запрос к API с ретраем через DoH при сбое DNS.

        Args:
            method: HTTP-метод ("GET" или "POST").
            path: Путь относительно base_url.
            json_body: Тело запроса для POST.
            params: Query-параметры.

        Returns:
            object: Разобранный JSON либо None, если источник недоступен.
        """
        url = f"{self.base_url}{path}"
        try:
            response = await self._send(
                self.session, method, url, json_body=json_body, params=params
            )
        except CurlTimeout as exc:
            raise ExternalServiceTimeoutError(service_name=self.provider_name) from exc
        except DNSError:
            resolved_session = await self._build_doh_session()
            if resolved_session is None:
                logger.warning("Hanime unreachable: DNS failed and DoH gave no answer")
                return None
            try:
                response = await self._send(
                    resolved_session, method, url, json_body=json_body, params=params
                )
            except CurlTimeout as exc:
                raise ExternalServiceTimeoutError(service_name=self.provider_name) from exc
            except RequestException as exc:
                logger.warning("Hanime API request failed after DoH: %s", exc)
                return None
        except RequestException as exc:
            logger.warning("Hanime API request failed: %s", exc)
            return None

        try:
            response.raise_for_status()
            return response.json()
        except (RequestException, ValueError) as exc:
            logger.warning("Hanime API bad response: %s", exc)
            return None

    @staticmethod
    async def _send(
        session: AsyncSession,
        method: str,
        url: str,
        *,
        json_body: dict | None,
        params: dict | None,
    ):
        """Отправляет один запрос выбранной сессией.

        Args:
            session: curl_cffi-сессия.
            method: HTTP-метод ("GET" или "POST").
            url: Абсолютный URL.
            json_body: Тело запроса для POST.
            params: Query-параметры.

        Returns:
            Response: Ответ curl_cffi.

        Raises:
            ExternalServiceUnavailableError: Когда метод не поддержан.
        """
        if method == "POST":
            return await session.post(url, json=json_body, params=params)
        if method == "GET":
            return await session.get(url, params=params)
        raise ExternalServiceUnavailableError(service_name="Hanime")

    async def _build_doh_session(self) -> AsyncSession | None:
        """Строит сессию с фиксированным IP хоста из DoH-ответа.

        Returns:
            AsyncSession | None: Сессия с RESOLVE-привязкой или None.
        """
        if self._resolve_session is not None:
            return self._resolve_session
        host = re.sub(r"^https?://", "", self.base_url).strip("/")
        address = await self._doh_lookup(host)
        if not address:
            return None
        kwargs = dict(self._session_kwargs)
        kwargs["curl_options"] = {CurlOpt.RESOLVE: [f"{host}:443:{address}"]}
        self._resolve_session = AsyncSession(**kwargs)
        return self._resolve_session

    async def _doh_lookup(self, host: str) -> str | None:
        """Резолвит A-запись через DNS-over-HTTPS Cloudflare.

        Args:
            host: Имя хоста без схемы.

        Returns:
            str | None: IPv4-адрес или None.
        """
        try:
            response = await self.session.get(
                _DOH_RESOLVER_URL,
                params={"name": host, "type": "A"},
                headers={"accept": "application/dns-json"},
            )
            response.raise_for_status()
            answers = response.json().get("Answer") or []
        except (RequestException, ValueError) as exc:
            logger.warning("DoH lookup failed for %s: %s", host, exc)
            return None
        for answer in answers:
            if isinstance(answer, dict) and answer.get("type") == 1:
                data = str(answer.get("data") or "").strip()
                if data:
                    return data
        return None
