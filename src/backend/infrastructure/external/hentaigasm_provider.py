"""Hentaigasm watch source provider (hentai/adult тайтлы).

Публичный сайт без капчи: поиск — ``GET /?s=<query>``, страница ролика —
``/slug/``, где прямой MP4 лежит в конфигурации jwplayer (``file: "..."``).
Ссылки на ``hgasm*.com`` не подписаны и не протухают, в отличие от
подписанных CDN-ссылок Eporner.
"""

from __future__ import annotations

import asyncio
import re

import httpx

from backend.domain.value_objects.watch.discovery import DiscoveredWatchSource
from backend.domain.value_objects.watch.translation_availability import (
    TranslationEpisodeAvailability,
)
from backend.infrastructure.external.errors import (
    ExternalServiceError,
    ExternalServiceTimeoutError,
    ExternalServiceUnavailableError,
)
from backend.infrastructure.external.watch_source_provider import WatchSourceProvider

_WORD_RE = re.compile(r"[a-z0-9а-яё]+", re.IGNORECASE)
#: Карточка ролика в выдаче: ``<a class="clip-link" ... title="..." href="...">``.
#: Намеренно не берётся общий ``<a href title>`` — им размечаются служебные
#: ссылки («Permalink to ...», «Posts by admin») и блоки, не являющиеся
#: результатами поиска по тайтлу.
_CLIP_HREF_RE = re.compile(
    r'<a[^>]+class="clip-link"[^>]*?title="(?P<title>[^"]+)"[^>]*?href="(?P<url>https?://[^"]+)"',
    re.I,
)
_FILE_RE = re.compile(r'file:\s*"(?P<url>https?://[^"]+\.(?:mp4|m3u8))"', re.I)
_QUALITY_RE = re.compile(r"\b(240|360|480|720|1080|2160)[pP]\b")
#: Номер части в заголовке ролика: «... Uncensored 2 Subbed», «... Episode 3».
_PART_NUMBER_RE = re.compile(
    r"(?:uncensored|episode|ep|part|vol(?:ume)?)\s*\.?\s*(\d{1,3})\b|\b(\d{1,3})\s+(?:subbed|uncensored)\b",
    re.I,
)

#: Стабильный псевдо-id дорожки: справочника переводов у сайта нет, весь
#: сайт выступает единственной озвучкой. Значение фиксировано, чтобы карта
#: доступности была детерминированной между запросами.
_TRANSLATION_ID = 2

#: Насколько много лишних слов допускается в названии ролика относительно
#: запроса. У Hentaigasm в заголовке почти всегда есть суффиксы вида
#: «Subbed»/«Uncensored», поэтому порог выше, чем у Eporner.
_MAX_EXTRA_WORDS = 5

#: Сколько карточек разбирается на странице выдачи до фильтрации. Поиск
#: сайта возвращает много нерелевантных роликов в начале списка, поэтому
#: смотреть только первые ``limit`` нельзя — релевантный тайтл туда не
#: попадёт. Страница отдаёт меньше 100 карточек, поэтому значения хватает
#: с запасом.
_SEARCH_SCAN_LIMIT = 95

#: Резолв страниц роликов намеренно последовательный: замер показал, что
#: сайт не держит параллельные обращения — из двух одновременных запросов
#: один стабильно уходил в таймаут на весь HENTAIGASM_TIMEOUT.
_RESOLVE_CONCURRENCY = 1

#: Сколько попыток делает один GET-запрос. Прокси флапает, поэтому повтор
#: почти всегда успевает там, где первая попытка упала по таймауту.
_REQUEST_ATTEMPTS = 3

#: Пауза перед повтором, умножается на номер попытки.
_RETRY_BACKOFF_SECONDS = 0.4

#: Потолок для connect-фазы запроса. Отдельный от общего таймаута: почти все
#: сбои здесь — это зависшее соединение до прокси, а не медленный ответ.
_CONNECT_TIMEOUT = 3.0

_BROWSER_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)


class HentaigasmProvider(WatchSourceProvider):
    """Ищет прямые MP4 на Hentaigasm через поиск по названию.

    Транспортные сбои транслируются в
    :mod:`backend.infrastructure.external.errors`; неожиданная форма ответа
    деградирует в пустой результат. Кандидаты фильтруются token-match по
    названию, чтобы не подменять тайтл похожим роликом.
    """

    def __init__(self, *, base_url: str, enabled: bool, timeout: float):
        self.base_url = base_url.rstrip("/")
        self.enabled = enabled
        self.timeout = timeout
        self.provider_name = "Hentaigasm"
        self.session = httpx.AsyncClient(
            # connect-квота заметно меньше общего: замеры показали, что почти
            # все сбои — это ConnectTimeout на прокси, а не медленный ответ
            # сервера. С connect=3 с зависшее соединение обрывается быстро и
            # успевает сработать ретрай, тогда как общий таймаут на том же
            # флапе съедал все секунды HENTAIGASM_TIMEOUT молча.
            timeout=httpx.Timeout(timeout, connect=min(float(timeout), _CONNECT_TIMEOUT)),
            # trust_env включён, как у Eporner: сайт недоступен напрямую из
            # ряда сетей и требует маршрута/прокси из доверенного окружения.
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
        """Проверяет, включён ли провайдер.

        Returns:
            bool: True когда провайдер включён и базовый URL задан.
        """
        return bool(self.enabled and self.base_url)

    async def search_sources(
        self,
        title: str,
        episode: int,
        year: int | None = None,
        limit: int = 8,
        shikimori_id: int | None = None,
    ) -> list[DiscoveredWatchSource]:
        """Ищет прямые MP4 по названию через поиск Hentaigasm.

        Args:
            title: Название тайтла.
            episode: Номер эпизода для результата.
            year: Год выпуска (игнорируется: у сайта нет года в выдаче).
            limit: Максимум роликов на выбор из поиска.
            shikimori_id: Внешний id (игнорируется: у сайта свои id,
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
            candidates = await self._search_page(query, per_page=_SEARCH_SCAN_LIMIT)
        except ExternalServiceError:
            return []

        discovered: list[DiscoveredWatchSource] = []
        seen_urls: set[str] = set()
        needed = max(int(limit), 1)
        part_index = 0
        for page_url, page_title in candidates:
            if not await self._is_relevant(query, page_title):
                continue
            if len(discovered) >= needed:
                break
            try:
                stream_url = await self._resolve_stream(page_url)
            except ExternalServiceError:
                continue
            if not stream_url or stream_url in seen_urls:
                continue
            seen_urls.add(stream_url)
            part_index += 1
            discovered.append(
                DiscoveredWatchSource(
                    episode=int(episode),
                    translation_name=self._translation_label(page_title, part_index),
                    translation_type="voice",
                    language="ja",
                    provider_name=self.provider_name,
                    source_name=page_url,
                    quality_label=self._quality_label(stream_url, page_title),
                    stream_url=stream_url,
                )
            )
        return discovered

    def _translation_label(self, page_title: str, part_index: int) -> str:
        """Собирает отображаемое имя дорожки для конкретного ролика.

        У сайта нет ни студий, ни «озвучек» — каждый ролик самостоятельный
        релиз. Раньше все они отдавались под одним именем ``Hentaigasm``, а
        страница просмотра группирует источники по имени озвучки и
        показывает первую строку группы, поэтому из десяти найденных
        роликов в интерфейсе был виден ровно один. Номер части берётся из
        заголовка («... Uncensored 2 Subbed»), а если его нет — из
        порядкового номера выдачи, чтобы имена всё равно различались.

        Args:
            page_title: Заголовок ролика из выдачи.
            part_index: Порядковый номер ролика (начиная с 1).

        Returns:
            str: Уникальное имя дорожки для этого ролика.
        """
        match = _PART_NUMBER_RE.search(str(page_title or ""))
        part = (
            next(
                (group for group in match.groups() if group),
                str(part_index),
            )
            if match
            else str(part_index)
        )
        return f"{self.provider_name} · часть {part}"

    async def get_translations_availability(
        self,
        title: str,
        year: int | None = None,
        shikimori_id: int | None = None,
    ) -> list[TranslationEpisodeAvailability]:
        """Строит карту доступности серий по хентай-тайтлу.

        У сайта нет нумерации эпизодов — ролики привязаны к тайтлу, а не к
        серии. Карта подтверждает наличие контента по названию и относит его к
        первой серии; без неё провайдер считался бы «не умеющим» и хентай
        отсекался фильтром «только с озвучкой».

        Args:
            title: Название тайтла.
            year: Год выпуска (игнорируется: у сайта нет года в выдаче).
            shikimori_id: Внешний id (игнорируется: у сайта свои id,
                текстовая адресация остаётся строгой по токенам).

        Returns:
            list[TranslationEpisodeAvailability]: Одна запись, если по
            тайтлу есть хотя бы один релевантный ролик, иначе пустой список.
        """
        if not await self.is_enabled():
            return []

        query = str(title or "").strip()
        if not query:
            return []
        try:
            candidates = await self._search_page(query, per_page=_SEARCH_SCAN_LIMIT)
        except ExternalServiceError:
            return []
        for page_url, page_title in candidates:
            if not await self._is_relevant(query, page_title):
                continue
            return [
                TranslationEpisodeAvailability(
                    translation_id=_TRANSLATION_ID,
                    title=self.provider_name,
                    translation_type="voice",
                    episodes_count=1,
                    available_episodes=[1],
                    link=page_url,
                )
            ]
        return []

    async def _search_page(self, query: str, per_page: int) -> list[tuple[str, str]]:
        """Возвращает пары (ссылка на страницу, заголовок) из поиска.

        Args:
            query: Поисковый запрос (название тайтла).
            per_page: Сколько роликов разобрать на странице.

        Returns:
            list[tuple[str, str]]: Пары (URL страницы, заголовок).

        Raises:
            ExternalServiceTimeoutError: Таймаут запроса.
            ExternalServiceUnavailableError: Сеть/HTTP-ошибка.
        """
        response = await self._get(self.base_url, params={"s": query})
        pairs: list[tuple[str, str]] = []
        seen: set[str] = set()
        for match in _CLIP_HREF_RE.finditer(response.text):
            page_url = match.group("url")
            if page_url in seen:
                continue
            seen.add(page_url)
            pairs.append((page_url, match.group("title")))
            if len(pairs) >= per_page:
                break
        return pairs

    async def _resolve_stream(self, page_url: str) -> str | None:
        """Достаёт прямую ссылку на файл со страницы ролика.

        Args:
            page_url: Страница ролика на сайте.

        Returns:
            str | None: Прямая ссылка на MP4/HLS или None, если её нет.

        Raises:
            ExternalServiceTimeoutError: Таймаут запроса.
            ExternalServiceUnavailableError: Сеть/HTTP-ошибка.
        """
        response = await self._get(page_url)
        match = _FILE_RE.search(response.text)
        return match.group("url") if match else None

    @staticmethod
    def _quality_label(stream_url: str, page_title: str) -> str:
        """Определяет подпись качества из ссылки или заголовка.

        Args:
            stream_url: Прямая ссылка на файл.
            page_title: Заголовок ролика.

        Returns:
            str: Метка качества или "auto", если качество не указано.
        """
        for source in (stream_url, page_title):
            match = _QUALITY_RE.search(source)
            if match:
                return f"{match.group(1)}p"
        return "auto"

    async def _is_relevant(self, title: str, item_title: str) -> bool:
        """Проверяет совпадение названия по токенам.

        Args:
            title: Запрошенное название.
            item_title: Заголовок ролика из выдачи.

        Returns:
            bool: True когда все слова запроса есть в заголовке и лишних
            слов немного.
        """
        query_tokens = set(_WORD_RE.findall(title.lower()))
        if not query_tokens:
            return False
        name_tokens = set(_WORD_RE.findall(str(item_title or "").lower()))
        if not name_tokens:
            return False
        missing = query_tokens - name_tokens
        extra = name_tokens - query_tokens
        return not missing and len(extra) <= _MAX_EXTRA_WORDS

    async def _get(self, url: str, *, params: dict[str, str] | None = None) -> httpx.Response:
        """GET-запрос с ретраями и трансляцией транспортных ошибок.

        Замеры показали, что локальный прокси, который httpx подхватывает из
        системных настроек при ``trust_env=True``, флапает: примерно треть
        запросов к сайту падает (``ConnectTimeout``/``ConnectError``/
        ``RemoteProtocolError``), причём таймауты съедали весь
        ``HENTAIGASM_TIMEOUT`` целиком. Без ретраев один сбойное соединение
        съедало страницу просмотра на десятки секунд и возвращало пустой
        результат, хотя следующий запрос проходил за доли секунды. Повтор
        с короткой паузой переживает такие всплески, не меняя итоговую
        семантику: успех отдаётся сразу, все попытки исчерпаны — та же
        доменная ошибка, что и раньше.

        Args:
            url: Абсолютный URL.
            params: Query-параметры.

        Returns:
            httpx.Response: Ответ сервиса.

        Raises:
            ExternalServiceTimeoutError: Таймаут запроса во всех попытках.
            ExternalServiceUnavailableError: Сеть/HTTP-ошибка во всех попытках.
        """
        last_error: ExternalServiceError | None = None
        for attempt in range(_REQUEST_ATTEMPTS):
            if attempt:
                await asyncio.sleep(_RETRY_BACKOFF_SECONDS * attempt)
            try:
                response = await self.session.get(url, params=params)
                response.raise_for_status()
                return response
            except httpx.TimeoutException as exc:
                last_error = ExternalServiceTimeoutError(service_name=self.provider_name)
                last_error.__cause__ = exc
            except httpx.HTTPError as exc:
                last_error = ExternalServiceUnavailableError(service_name=self.provider_name)
                last_error.__cause__ = exc
        if last_error is not None:
            raise last_error
        raise ExternalServiceUnavailableError(service_name=self.provider_name)
