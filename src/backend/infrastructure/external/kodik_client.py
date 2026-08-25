import asyncio
import base64
import json
import re
import time
from urllib.parse import urlencode, urljoin

import httpx

from backend.config import Settings
from backend.domain.value_objects.watch.discovery import DiscoveredWatchSource
from backend.infrastructure.external.errors import ExternalServiceError
from backend.infrastructure.external.http_guard import read_json_limited
from backend.infrastructure.external.kodik_token_store import KodikTokenStore
from backend.infrastructure.external.watch_source_provider import WatchSourceProvider

_PROBE_BACKOFF_SECONDS = 300.0
_MAX_SEARCH_PAGES = 20
_LINKS_CONCURRENCY = 8


class KodikClient(WatchSourceProvider):
    """Ищет материалы Kodik и извлекает прямые HLS-ссылки."""

    _link_pattern = re.compile(
        r"^(?:https?:|)//(?P<host>[a-z0-9.-]+\.[a-z]+)"
        r"/(?P<kind>[a-z-]+)/(?P<material_id>\d+)/(?P<hash>[0-9a-z]+)/(?P<quality>\d+p)(?:.*)$",
        re.IGNORECASE,
    )

    def __init__(self):
        self.api_token = Settings.kodik_api_token
        self.api_url = Settings.kodik_api_url.rstrip("/")
        self.provider_name = "Kodik"
        self.default_video_info_endpoint = "/ftor"
        self.session = httpx.AsyncClient(
            timeout=httpx.Timeout(6),
            trust_env=False,
            follow_redirects=True,
        )
        self._working_token: str | None = None
        self._probe_retry_at: float = 0.0
        self._token_store = KodikTokenStore(
            tokens_path=Settings.kodik_tokens_path,
            configured_token=self.api_token,
        )

    async def is_enabled(self) -> bool:
        return bool(self.api_token) or bool(await self._token_store.candidates())

    async def is_configured(self) -> bool:
        return await self.is_enabled()

    async def aclose(self) -> None:
        """Close the underlying HTTP client."""
        await self.session.aclose()

    async def _probe_token(self, token: str) -> bool:
        """Проверяет токен на живом API (всего один лёгкий запрос)."""
        probe_params: dict[str, str | int] = {
            "token": token,
            "title": "test",
            "episode": 1,
            "limit": 1,
        }
        try:
            response = await self.session.get(
                f"{self.api_url}/search",
                params=probe_params,
            )
            status_code = getattr(response, "status_code", 200)
            if status_code != 200:
                return False
            payload = response.json()
        except (httpx.HTTPError, ValueError, TypeError):
            return False
        if await KodikTokenStore.token_looks_invalid(payload):
            return False
        return True

    async def _resolve_token(self) -> str | None:
        """Возвращает подтверждённый рабочий токен или None в режиме backoff.

        Если все кандидаты недавно провалили probe-запрос, повторные проверки
        не выполняются до истечения backoff-окна: так недоступный Kodik не
        замедляет каждый поиск.
        """
        if self._working_token:
            return self._working_token
        if time.monotonic() < self._probe_retry_at:
            return None
        for token in await self._token_store.candidates():
            if await self._probe_token(token):
                self._working_token = token
                return token
        self._probe_retry_at = time.monotonic() + _PROBE_BACKOFF_SECONDS
        return None

    async def search_sources(
        self,
        title: str,
        episode: int,
        year: int | None = None,
        limit: int = 100,
    ) -> list[DiscoveredWatchSource]:
        """Ищет источники эпизода через Kodik и возвращает доступные качества."""
        if not await self.is_enabled():
            return []

        token = await self._resolve_token()
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
            material_link = await self._extract_episode_link(
                material=material, episode=episode
            ) or material.get("link")
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

    async def _collect_video_links(
        self, materials: list[dict], episode: int
    ) -> list[dict[str, list[dict[str, str]]]]:
        """Извлекает ссылки качества для всех материалов с ограничением параллелизма."""
        semaphore = asyncio.Semaphore(_LINKS_CONCURRENCY)

        async def fetch(material: dict) -> dict[str, list[dict[str, str]]]:
            material_link = await self._extract_episode_link(
                material=material, episode=episode
            ) or material.get("link")
            if not material_link:
                return {}
            async with semaphore:
                return await self._get_video_links(str(material_link))

        return list(await asyncio.gather(*(fetch(material) for material in materials)))

    async def _looks_relevant(
        self,
        material: dict,
        requested_title: str,
        requested_year: int | None,
    ) -> bool:
        material_year = material.get("year")
        if (
            requested_year
            and isinstance(material_year, int)
            and abs(material_year - requested_year) > 1
        ):
            return False

        normalized_requested = await self._normalize_title(requested_title)
        if not normalized_requested:
            return False
        candidates = [
            material.get("title"),
            material.get("title_orig"),
            material.get("other_title"),
        ]
        material_data = material.get("material_data") or {}
        candidates.extend(
            [
                material_data.get("title"),
                material_data.get("anime_title"),
                material_data.get("title_en"),
            ]
        )
        for candidate in candidates:
            normalized_candidate = await self._normalize_title(candidate)
            if not normalized_candidate:
                continue
            if normalized_candidate == normalized_requested:
                return True
            ratio = self._similarity_ratio(normalized_requested, normalized_candidate)
            if ratio >= 0.85:
                return True

        return False

    @staticmethod
    def _similarity_ratio(a: str, b: str) -> float:
        if not a or not b:
            return 0.0
        if a == b:
            return 1.0
        if len(a) < 3 or len(b) < 3:
            return 1.0 if a == b else 0.0
        if a in b or b in a:
            shorter = min(len(a), len(b))
            longer = max(len(a), len(b))
            return shorter / longer
        words_a = set(a.split())
        words_b = set(b.split())
        if not words_a or not words_b:
            return 0.0
        intersection = words_a & words_b
        union = words_a | words_b
        return len(intersection) / len(union)

    async def _extract_episode_link(self, material: dict, episode: int) -> str | None:
        seasons = material.get("seasons") or {}
        if not isinstance(seasons, dict) or not seasons:
            return None

        preferred_keys: list[str] = []
        last_season = material.get("last_season")
        if last_season is not None:
            preferred_keys.append(str(last_season))
        preferred_keys.extend(
            sorted(
                seasons.keys(), key=lambda value: (int(value) if value.isdigit() else 10**9, value)
            )
        )

        for season_key in preferred_keys:
            season = seasons.get(season_key)
            if not isinstance(season, dict):
                continue
            episodes = season.get("episodes") or {}
            if not isinstance(episodes, dict):
                continue
            raw_episode = episodes.get(str(episode)) or episodes.get(episode)
            if isinstance(raw_episode, str):
                return raw_episode
            if isinstance(raw_episode, dict):
                return raw_episode.get("link")
        return None

    async def _get_video_links(self, link: str) -> dict[str, list[dict[str, str]]]:
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

    async def _parse_link(self, link: str) -> dict[str, str] | None:
        match = self._link_pattern.match(link)
        if not match:
            return None
        return {
            "host": match.group("host"),
            "type": match.group("kind"),
            "id": match.group("material_id"),
            "hash": match.group("hash"),
            "quality": match.group("quality"),
        }

    async def _get_actual_video_info_endpoint(self, normalized_link: str) -> str | None:
        try:
            player_page = await self.session.get(
                normalized_link,
            )
            player_page.raise_for_status()
            page_text = player_page.text
        except httpx.HTTPError:
            return None

        player_chunk_match = re.search(
            r'src="(?P<link>/assets/js/app\.player_single\.[a-z0-9]+\.js)"',
            page_text,
            flags=re.IGNORECASE,
        )
        if not player_chunk_match:
            return None

        chunk_url = urljoin(normalized_link, player_chunk_match.group("link"))
        try:
            chunk_response = await self.session.get(
                chunk_url,
            )
            chunk_response.raise_for_status()
            chunk_text = chunk_response.text
        except httpx.HTTPError:
            return None

        endpoint_match = re.search(
            r'type:"POST",url:atob\("(?P<b64str>[^"]+)"\)',
            chunk_text,
            flags=re.IGNORECASE,
        )
        if not endpoint_match:
            return "/kor"

        try:
            decoded = base64.b64decode(endpoint_match.group("b64str")).decode("utf-8")
        except (ValueError, UnicodeDecodeError):
            return "/kor"
        return decoded or "/kor"

    async def _decode_kodik_src(self, encoded_src: str) -> str | None:
        shifted = []
        for char in encoded_src:
            if "A" <= char <= "Z":
                code = ord(char) + 18
                if code > ord("Z"):
                    code -= 26
                shifted.append(chr(code))
                continue
            if "a" <= char <= "z":
                code = ord(char) + 18
                if code > ord("z"):
                    code -= 26
                shifted.append(chr(code))
                continue
            shifted.append(char)

        try:
            shifted_text = "".join(shifted)
            padding = (-len(shifted_text)) % 4
            return base64.b64decode(shifted_text + "=" * padding).decode("utf-8")
        except (ValueError, UnicodeDecodeError):
            return None

    async def _normalize_link(self, value: str | None) -> str | None:
        if not value:
            return None
        text = str(value).strip()
        if text.startswith("//"):
            return f"https:{text}"
        if text.startswith("/"):
            return f"https://kodikplayer.com{text}"
        return text

    async def _normalize_title(self, title: str | None) -> str:
        text = str(title or "").lower().strip()
        text = re.sub(r"[^a-zа-я0-9]+", " ", text, flags=re.IGNORECASE)
        return " ".join(text.split())

    async def _map_translation_type(self, value: str) -> str:
        lowered = value.lower()
        if lowered == "subtitles":
            return "sub"
        return lowered or "voice"
