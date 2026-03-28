import base64
import json
import re
from urllib.parse import urlencode, urljoin

import requests

from src.backend.dependencies.settings import Settings
from src.backend.domain.watch.value_object import DiscoveredWatchSource
from src.backend.infrastructure.external.watch_source_provider import (
    WatchSourceProvider,
)


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
        self.session = requests.Session()
        self.session.trust_env = False

    def is_enabled(self) -> bool:
        return bool(self.api_token)

    def is_configured(self) -> bool:
        return self.is_enabled()

    def search_sources(
        self,
        title: str,
        episode: int,
        year: int | None = None,
        limit: int = 24,
    ) -> list[DiscoveredWatchSource]:
        """Ищет источники эпизода через Kodik и возвращает доступные качества."""
        if not self.is_enabled():
            return []

        params: dict[str, str | int | bool] = {
            "token": self.api_token or "",
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

        try:
            response = self.session.get(
                f"{self.api_url}/search",
                params=params,
                timeout=25,
            )
            response.raise_for_status()
            payload = response.json()
        except (requests.RequestException, ValueError, TypeError):
            return []

        results = payload.get("results", []) or []
        discovered: list[DiscoveredWatchSource] = []
        seen: set[tuple[str, str, str]] = set()
        for material in results:
            if not self._looks_relevant(
                material=material, requested_title=title, requested_year=year
            ):
                continue
            material_link = self._extract_episode_link(
                material=material, episode=episode
            ) or material.get("link")
            if not material_link:
                continue

            translation = material.get("translation") or {}
            translation_name = (
                str(translation.get("title") or "Unknown").strip() or "Unknown"
            )
            translation_type = self._map_translation_type(
                str(translation.get("type") or "voice").strip()
            )
            source_name = str(material.get("id") or material_link).strip()
            quality_map = self._get_video_links(material_link)
            if not quality_map:
                continue

            for quality_label, sources in quality_map.items():
                for source in sources:
                    stream_url = self._normalize_link(source.get("src"))
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

    def _looks_relevant(
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

        normalized_requested = self._normalize_title(requested_title)
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
            normalized_candidate = self._normalize_title(candidate)
            if normalized_candidate and (
                normalized_requested in normalized_candidate
                or normalized_candidate in normalized_requested
            ):
                return True

        return requested_year is None and bool(material.get("link"))

    def _extract_episode_link(self, material: dict, episode: int) -> str | None:
        seasons = material.get("seasons") or {}
        if not isinstance(seasons, dict) or not seasons:
            return None

        preferred_keys: list[str] = []
        last_season = material.get("last_season")
        if last_season is not None:
            preferred_keys.append(str(last_season))
        preferred_keys.extend(sorted(seasons.keys(), key=self._season_sort_key))

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

    def _get_video_links(self, link: str) -> dict[str, list[dict[str, str]]]:
        normalized_link = self._normalize_link(link)
        if not normalized_link:
            return {}

        parsed = self._parse_link(normalized_link)
        if not parsed:
            return {}

        links = self._request_video_links(
            host=parsed["host"],
            params={
                key: value
                for key, value in parsed.items()
                if key not in {"host", "quality"}
            },
            endpoint=self.default_video_info_endpoint,
        )
        if not links:
            actual_endpoint = self._get_actual_video_info_endpoint(normalized_link)
            if actual_endpoint and actual_endpoint != self.default_video_info_endpoint:
                links = self._request_video_links(
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
                decoded_src = self._decode_kodik_src(str(encoded_src))
                if not decoded_src:
                    continue
                decoded_items.append(
                    {
                        "src": self._normalize_link(decoded_src),
                        "type": str(item.get("type") or "application/x-mpegURL"),
                    }
                )
            if decoded_items:
                decoded_links[str(quality_label)] = decoded_items
        return decoded_links

    def _request_video_links(
        self,
        host: str,
        params: dict[str, str],
        endpoint: str,
    ) -> dict[str, list[dict[str, str]]] | None:
        video_info_url = f"https://{host}{endpoint}?{urlencode(params)}"
        try:
            response = self.session.get(
                video_info_url,
                timeout=25,
            )
            response.raise_for_status()
            payload = response.json()
        except (requests.RequestException, ValueError, TypeError, json.JSONDecodeError):
            return None

        links = payload.get("links")
        return links if isinstance(links, dict) else None

    def _parse_link(self, link: str) -> dict[str, str] | None:
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

    def _get_actual_video_info_endpoint(self, normalized_link: str) -> str | None:
        try:
            player_page = self.session.get(
                normalized_link,
                timeout=25,
            )
            player_page.raise_for_status()
            page_text = player_page.text
        except requests.RequestException:
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
            chunk_response = self.session.get(
                chunk_url,
                timeout=25,
            )
            chunk_response.raise_for_status()
            chunk_text = chunk_response.text
        except requests.RequestException:
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

    def _decode_kodik_src(self, encoded_src: str) -> str | None:
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
            return base64.b64decode("".join(shifted)).decode("utf-8")
        except (ValueError, UnicodeDecodeError):
            return None

    def _normalize_link(self, value: str | None) -> str | None:
        if not value:
            return None
        text = str(value).strip()
        if text.startswith("//"):
            return f"https:{text}"
        if text.startswith("/"):
            return f"https://kodikplayer.com{text}"
        return text

    def _normalize_title(self, title: str | None) -> str:
        text = str(title or "").lower().strip()
        text = re.sub(r"[^a-zа-я0-9]+", " ", text, flags=re.IGNORECASE)
        return " ".join(text.split())

    def _map_translation_type(self, value: str) -> str:
        lowered = value.lower()
        if lowered == "subtitles":
            return "sub"
        return lowered or "voice"

    def _season_sort_key(self, value: str) -> tuple[int, str]:
        try:
            return int(value), value
        except ValueError:
            return 10**9, value
