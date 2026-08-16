import re

import requests

from backend.config import Settings
from backend.domain.watch.value_object import DiscoveredWatchSource
from backend.infrastructure.external._async import external_method
from backend.infrastructure.external.watch_source_provider import WatchSourceProvider


class JustWatchClient(WatchSourceProvider):
    """Ищет официальные внешние офферы по тайтлу через JustWatch Partner API."""

    def __init__(self):
        self.partner_token = Settings.justwatch_partner_token
        self.api_url = Settings.justwatch_api_url.rstrip("/")
        self.locale = Settings.justwatch_locale
        self.provider_name = "JustWatch"
        self._provider_cache: dict[int, str] | None = None
        self.session = requests.Session()
        self.session.trust_env = False

    def is_enabled(self) -> bool:
        """Возвращает доступность JustWatch-провайдера."""
        return bool(self.partner_token)

    @external_method
    def search_sources(
        self,
        title: str,
        episode: int,
        year: int | None = None,
        limit: int = 8,
    ) -> list[DiscoveredWatchSource]:
        """Возвращает внешние офферы просмотра для тайтла."""
        if not self.is_enabled() or not year:
            return []

        payload = self._get_offers(title=title, year=year)
        if not payload:
            return []

        offers = payload.get("offers") or []
        if not isinstance(offers, list):
            return []

        provider_map = self._get_provider_map()
        title_label = str(
            payload.get("title")
            or payload.get("original_title")
            or payload.get("full_path")
            or title
        ).strip()
        discovered: list[DiscoveredWatchSource] = []
        seen: set[tuple[str, str, str]] = set()
        for offer in offers:
            if not isinstance(offer, dict):
                continue
            target_url = self._extract_offer_url(offer)
            provider_name = provider_map.get(int(offer.get("provider_id") or 0))
            if not target_url or not provider_name:
                continue
            quality_label = self._format_offer_label(offer)
            dedupe_key = (provider_name, target_url, quality_label)
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)
            discovered.append(
                DiscoveredWatchSource(
                    episode=episode,
                    translation_name=provider_name,
                    translation_type="external",
                    provider_name=self.provider_name,
                    source_name=title_label,
                    quality_label=quality_label,
                    stream_url=target_url,
                    source_type="external",
                    language="und",
                )
            )
            if len(discovered) >= limit:
                break
        return discovered

    def _get_offers(self, title: str, year: int) -> dict | None:
        """Запрашивает офферы просмотра для сериала по названию и году релиза."""
        try:
            response = self.session.get(
                f"{self.api_url}/offers/object_type/show/locale/{self.locale}",
                params={
                    "token": self.partner_token or "",
                    "title": title,
                    "release_year": int(year),
                },
                timeout=6,
            )
            response.raise_for_status()
            payload = response.json()
        except (requests.RequestException, ValueError, TypeError):
            return None
        return payload if isinstance(payload, dict) else None

    def _get_provider_map(self) -> dict[int, str]:
        """Подтягивает и кеширует карту provider_id -> название провайдера."""
        if self._provider_cache is not None:
            return self._provider_cache

        try:
            response = self.session.get(
                f"{self.api_url}/providers/locale/{self.locale}",
                params={"token": self.partner_token or ""},
                timeout=6,
            )
            response.raise_for_status()
            payload = response.json()
        except (requests.RequestException, ValueError, TypeError):
            self._provider_cache = {}
            return self._provider_cache

        if isinstance(payload, list):
            self._provider_cache = {
                int(item.get("id") or 0): str(
                    item.get("clear_name") or item.get("short_name") or ""
                ).strip()
                for item in payload
                if isinstance(item, dict)
                and item.get("id") is not None
                and str(item.get("clear_name") or item.get("short_name") or "").strip()
            }
        else:
            self._provider_cache = {}
        return self._provider_cache

    def _extract_offer_url(self, offer: dict) -> str | None:
        """Извлекает переход на внешний сервис из объекта оффера."""
        urls = offer.get("urls") or {}
        if not isinstance(urls, dict):
            return None
        for key in ("standard_web", "deeplink_web", "deep_link_android_tv", "web"):
            value = urls.get(key)
            if not value:
                continue
            return str(value).strip()
        return None

    def _format_offer_label(self, offer: dict) -> str:
        """Формирует компактную подпись оффера для селекта качества/варианта."""
        monetization = str(offer.get("monetization_type") or "").strip().lower()
        presentation = str(offer.get("presentation_type") or "").strip().lower()
        package = str(offer.get("package_short_name") or "").strip()
        parts = [
            self._humanize_token(monetization),
            self._humanize_token(presentation),
            package,
        ]
        return " • ".join(part for part in parts if part) or "Open"

    def _humanize_token(self, value: str | None) -> str:
        """Преобразует технический токен оффера в читаемую подпись."""
        text = str(value or "").strip()
        if not text:
            return ""
        text = re.sub(r"[_-]+", " ", text)
        return " ".join(part.capitalize() for part in text.split())
