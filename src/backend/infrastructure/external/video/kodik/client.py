"""Сетевой слой клиента Kodik: токены, поиск и списки качества.

Модуль отвечает за HTTP-взаимодействие с API Kodik. Разбор ответов и
сопоставление названий живут в :mod:`backend.infrastructure.external.video.kodik.parsing`,
подбор токена — в :mod:`token_manager`, поиск ручки списка качеств — в
:mod:`endpoint_discovery`.
"""

import json
import re
from urllib.parse import urlencode

import httpx

from backend.application.interface.services import WatchSourceProviderInterface
from backend.config import Settings
from backend.domain.value_objects.watch.discovery import DiscoveredWatchSource
from backend.domain.value_objects.watch.translation_availability import (
    TranslationEpisodeAvailability,
)
from backend.infrastructure.external._common import ExternalServiceError, read_json_limited
from backend.infrastructure.external.video.kodik.endpoint_discovery import (
    DEFAULT_VIDEO_INFO_ENDPOINT,
    discover_video_info_endpoint,
)
from backend.infrastructure.external.video.kodik.mapping import (
    map_kodik_translations_to_episodes,
)
from backend.infrastructure.external.video.kodik.parsing import KodikParsingMixin
from backend.infrastructure.external.video.kodik.token_manager import KodikTokenManager
from backend.infrastructure.external.video.kodik.token_store import KodikTokenStore

_MAX_SEARCH_PAGES = 20


class KodikClient(WatchSourceProviderInterface, KodikParsingMixin):
    """Ищет материалы Kodik и извлекает прямые HLS-ссылки.

    Этот модуль отвечает за сеть: подбор токена с backoff'ом, пагинацию поиска и
    запросы списков качества. Разбор полученных ответов, сопоставление названий и
    нормализация ссылок вынесены в :class:`KodikParsingMixin` (модуль `parsing`),
    куда входят и правила сверки тайтлов.
    """

    _link_pattern = re.compile(
        r"^(?:https?:|)//(?P<host>[a-z0-9.-]+\.[a-z]+)"
        r"/(?P<kind>[a-z-]+)/(?P<material_id>\d+)/(?P<hash>[0-9a-z]+)/(?P<quality>\d+p)(?:.*)$",
        re.IGNORECASE,
    )

    def __init__(self):
        """Создать клиент, прочитав адрес API и хранилище токенов из конфига."""
        self.api_token = Settings.kodik_api_token
        self.api_url = Settings.kodik_api_url.rstrip("/")
        self.provider_name = "Kodik"
        self.default_video_info_endpoint = DEFAULT_VIDEO_INFO_ENDPOINT
        self.session = httpx.AsyncClient(
            timeout=httpx.Timeout(6),
            trust_env=False,
            follow_redirects=True,
        )
        self._tokens = KodikTokenManager(
            session=self.session,
            api_url=self.api_url,
            token_store=KodikTokenStore(
                tokens_path=Settings.kodik_tokens_path,
                configured_token=self.api_token,
            ),
            configured_token=self.api_token,
        )

    @property
    def _working_token(self) -> str | None:
        """Подтверждённый токен, если он уже найден.

        Returns:
            str | None: Рабочий токен или None.
        """
        return self._tokens.working_token

    @_working_token.setter
    def _working_token(self, value: str | None) -> None:
        """Запоминает подтверждённый токен.

        Args:
            value: Токен, который точно работает.
        """
        self._tokens.working_token = value

    async def is_enabled(self) -> bool:
        """Проверить, есть ли хоть один токен для запросов.

        Returns:
            bool: True, если задан токен из конфига или найден файл-хранилище
            с кандидатами.
        """
        return await self._tokens.is_enabled()

    async def is_configured(self) -> bool:
        """Проверить готовность провайдера к работе.

        Returns:
            bool: True, если клиент включён (см. :meth:`is_enabled`).
        """
        return await self.is_enabled()

    async def aclose(self) -> None:
        """Закрыть общий HTTP-клиент."""
        await self.session.aclose()

    async def search_sources(
        self,
        title: str,
        episode: int,
        year: int | None = None,
        limit: int = 100,
        shikimori_id: int | None = None,
    ) -> list[DiscoveredWatchSource]:
        """Ищет источники эпизода через Kodik и возвращает доступные качества.

        Адресация ведётся всегда по названию + строгой сверке релевантности
        (:meth:`_looks_relevant`). ``shikimori_id`` намеренно не передаётся
        в запрос: внешний id каталога может оказаться AniList-id, а Kodik
        ожидает MAL/Shikimori-id, и неверный id привёл бы к подмене контента
        либо пустому результату без какой-либо сверки по названию.

        Args:
            title: Название тайтла для поиска.
            episode: Номер эпизода.
            year: Год выпуска для смягчённой сверки.
            limit: Максимум материалов в выдаче.
            shikimori_id: Внешний id тайтла; не используется — см. выше,
                адресация остаётся только по названию.
        """
        if not await self.is_enabled():
            return []

        token = await self._tokens.resolve()
        if not token:
            return []

        params: dict[str, str | int | bool] = {
            "token": token,
            "title": title,
            "episode": max(int(episode), 1),
            "limit": max(int(limit), 1),
            "camrip": "false",
            "strict": "false",
            "with_material_data": "true",
            "with_seasons": "true",
            "with_episodes": "true",
            "with_episodes_data": "true",
        }
        if year:
            params["year"] = year

        materials = await self._search_all_pages(params)
        if not materials:
            return []

        relevant: list[tuple[dict, str, str, str]] = []
        for material in materials:
            if not await self._looks_relevant(
                material=material, requested_title=title, requested_year=year
            ):
                continue
            material_link = await self._extract_episode_link(material=material, episode=episode)
            if not material_link:
                continue

            translation = material.get("translation") or {}
            translation_name = str(translation.get("title") or "Unknown").strip() or "Unknown"
            translation_type = await self._map_translation_type(
                str(translation.get("type") or "voice").strip()
            )
            source_name = str(material.get("id") or material_link).strip()
            relevant.append((material, translation_name, translation_type, source_name))

        quality_maps = await self._collect_video_links([entry[0] for entry in relevant], episode)

        discovered: list[DiscoveredWatchSource] = []
        seen: set[tuple[str, str, str]] = set()
        for (_material, translation_name, translation_type, source_name), quality_map in zip(
            relevant, quality_maps
        ):
            for quality_label, sources in (quality_map or {}).items():
                for source in sources:
                    stream_url = await self._normalize_link(source.get("src"))
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
                            translation_type=translation_type,
                            provider_name=self.provider_name,
                            source_name=source_name,
                            quality_label=str(quality_label),
                            stream_url=stream_url,
                        )
                    )
        return discovered

    async def get_translations_availability(
        self,
        title: str,
        year: int | None = None,
        shikimori_id: int | None = None,
    ) -> list[TranslationEpisodeAvailability]:
        """Строит карту доступности серий по озвучкам тайтла.

        ``shikimori_id`` используется как доп. уточнение запроса, когда он
        есть (MAL/Shikimori-id в Kodik). Выдача при этом дополнительно
        проверяется на пересечение токенов названия (:meth:`_has_token_overlap`):
        если id оказался не того пространства (например, AniList-id,
        указывающий на другое аниме), материалы чужого тайтла будут
        отброшены и здоровый пустой результат предотвратит подмену контента.
        Без id выполняется строгий title-match (:meth:`_looks_relevant`).

        Args:
            title: Название тайтла.
            year: Год выпуска для смягчённой сверки.
            shikimori_id: Внешний id тайтла (MAL/Shikimori), если известен.

        Returns:
            list[TranslationEpisodeAvailability]: Карта доступности серий
            по озвучкам; пустой список, если Kodik недоступен.
        """
        if not await self.is_enabled():
            return []
        token = await self._tokens.resolve()
        if not token:
            return []

        params: dict[str, str | int | bool] = {
            "token": token,
            "with_material_data": "true",
            "with_seasons": "true",
            "with_episodes": "true",
            "with_episodes_data": "true",
            "limit": 100,
        }
        if shikimori_id:
            params["shikimori_id"] = int(shikimori_id)
        else:
            params["title"] = title
            if year:
                params["year"] = year

        materials = await self._search_all_pages(params)
        if not materials:
            return []

        if shikimori_id:
            filtered = [
                material
                for material in materials
                if await self._has_token_overlap(material=material, requested_title=title)
            ]
        else:
            filtered = [
                material
                for material in materials
                if await self._looks_relevant(
                    material=material, requested_title=title, requested_year=year
                )
            ]
        return map_kodik_translations_to_episodes({"results": filtered})

    async def _search_all_pages(self, base_params: dict[str, str | int | bool]) -> list[dict]:
        """Обходит все страницы поисковой выдачи Kodik (до ``_MAX_SEARCH_PAGES``)."""
        materials: list[dict] = []
        params = dict(base_params)
        for _page in range(_MAX_SEARCH_PAGES):
            try:
                response = await self.session.get(f"{self.api_url}/search", params=params)
                response.raise_for_status()
                payload = read_json_limited(response, service_name=self.provider_name)
            except (httpx.HTTPError, ValueError, TypeError, ExternalServiceError):
                break
            page_results = payload.get("results", []) or []
            materials.extend(item for item in page_results if isinstance(item, dict))
            next_page = payload.get("next_page")
            if not next_page:
                break
            params = {**base_params, "next": str(next_page).rsplit("=", 1)[-1]}
        return materials

    async def _get_video_links(self, link: str) -> dict[str, list[dict[str, str]]]:
        """Получить список качеств материала и раскодировать ссылки.

        Сначала пробуется штатный endpoint ``/ftor``; если Kodik его
        переименовал, адрес вычисляется по JS-бандлу плеера
        (:meth:`_get_actual_video_info_endpoint`) и запрос повторяется. Каждый
        ``src`` раскодируется и нормализуется, поэтому наружу уходят готовые
        ссылки.

        Args:
            link: Ссылка на материал Kodik.

        Returns:
            dict[str, list[dict[str, str]]]: Качество → список источников
            (``src``, ``type``). Пустой словарь, если материал не разобран.
        """
        normalized_link = await self._normalize_link(link)
        if not normalized_link:
            return {}

        parsed = await self._parse_link(normalized_link)
        if not parsed:
            return {}

        links = await self._request_video_links(
            host=parsed["host"],
            params={key: value for key, value in parsed.items() if key not in {"host", "quality"}},
            endpoint=self.default_video_info_endpoint,
        )
        if not links:
            actual_endpoint = await self._get_actual_video_info_endpoint(normalized_link)
            if actual_endpoint and actual_endpoint != self.default_video_info_endpoint:
                links = await self._request_video_links(
                    host=parsed["host"],
                    params={
                        key: value
                        for key, value in parsed.items()
                        if key not in {"host", "quality"}
                    },
                    endpoint=actual_endpoint,
                )
        if not isinstance(links, dict):
            return {}

        decoded_links: dict[str, list[dict[str, str]]] = {}
        for quality_label, items in links.items():
            if not isinstance(items, list):
                continue
            decoded_items: list[dict[str, str]] = []
            for item in items:
                if not isinstance(item, dict):
                    continue
                encoded_src = item.get("src")
                if not encoded_src:
                    continue
                decoded_src = await self._decode_kodik_src(str(encoded_src))
                if not decoded_src:
                    continue
                decoded_items.append(
                    {
                        "src": await self._normalize_link(decoded_src),
                        "type": str(item.get("type") or "application/x-mpegURL"),
                    }
                )
            if decoded_items:
                decoded_links[str(quality_label)] = decoded_items
        return decoded_links

    async def _request_video_links(
        self,
        host: str,
        params: dict[str, str],
        endpoint: str,
    ) -> dict[str, list[dict[str, str]]] | None:
        """Запросить список качеств с endpoint'а Kodik с одним повтором.

        Args:
            host: Хост материала Kodik.
            params: Параметры материала (id, kind, hash, translation и т.д.).
            endpoint: Путь ручки списка качеств.

        Returns:
            dict[str, list[dict[str, str]]] | None: Словарь ссылок либо None,
            если обе попытки завершились ошибкой.
        """
        video_info_url = f"https://{host}{endpoint}?{urlencode(params)}"
        for _attempt in range(2):
            try:
                response = await self.session.get(
                    video_info_url,
                )
                response.raise_for_status()
                payload = read_json_limited(response, service_name=self.provider_name)
                links = payload.get("links")
                return links if isinstance(links, dict) else None
            except (
                httpx.HTTPError,
                ValueError,
                TypeError,
                json.JSONDecodeError,
                ExternalServiceError,
            ):
                continue
        return None

    async def _get_actual_video_info_endpoint(self, normalized_link: str) -> str | None:
        """Вычисляет актуальный endpoint списка качества у Kodik.

        Args:
            normalized_link: Ссылка на материал Kodik.

        Returns:
            str | None: Путь endpoint'а либо None, если страницу или бандл не отдали.
        """
        return await discover_video_info_endpoint(self.session, normalized_link)
