import re

from src.backend.domain.anime.entity import Anime
from src.backend.domain.watch.entity import Translation, WatchSource
from src.backend.domain.watch.policy import (
    canonicalize_translation_name,
    get_translation_priority,
)
from src.backend.domain.watch.value_object import DiscoveredWatchSource
from src.backend.infrastructure.external.watch_source_provider import (
    WatchSourceProvider,
)
from src.backend.infrastructure.cache.ttl_cache import TTLCache
from src.backend.repository.watch_repository import WatchRepository


class WatchSourceSyncService:
    """Синхронизирует источники просмотра из внешнего провайдера в локальное хранилище."""

    def __init__(
        self, watch_repo: WatchRepository, providers: list[WatchSourceProvider]
    ):
        self.watch_repo = watch_repo
        self.providers = providers
        self.empty_result_cache = TTLCache[
            tuple[str, int, int, int | None, tuple[str, ...]],
            bool,
        ](
            ttl_seconds=600,
            max_entries=512,
        )

    def is_enabled(self) -> bool:
        return any(provider.is_enabled() for provider in self.providers)

    def get_enabled_provider_names(self) -> list[str]:
        return [
            provider.provider_name
            for provider in self.providers
            if provider.is_enabled()
        ]

    def get_provider_label(self) -> str | None:
        enabled = self.get_enabled_provider_names()
        return ", ".join(enabled) if enabled else None

    def sync_for_anime(
        self,
        anime_id: int,
        anime: Anime | None,
        episode: int,
        force: bool = False,
    ) -> list[WatchSource]:
        """Подтягивает и сохраняет источники для конкретного аниме и эпизода."""
        existing = self.watch_repo.get_sources(anime_id=anime_id, episode=episode)
        if not anime or not anime.title or not self.is_enabled():
            return existing

        existing_provider_names = {
            str(source.provider_name).strip().lower() for source in existing
        }
        providers_to_query = [
            provider
            for provider in self.providers
            if provider.is_enabled()
            and (
                force
                or provider.provider_name.strip().lower() not in existing_provider_names
            )
        ]
        if not providers_to_query:
            return existing

        title_variants = self._build_title_variants(anime.title)
        for provider in providers_to_query:
            empty_cache_key = (
                provider.provider_name.strip().lower(),
                int(anime_id),
                int(episode),
                anime.year,
                tuple(title_variants),
            )
            if not force and self.empty_result_cache.contains(empty_cache_key):
                continue

            discovered = self._discover_sources(
                provider=provider,
                title_variants=title_variants,
                episode=episode,
                year=anime.year,
            )
            if not discovered:
                self.empty_result_cache.set(empty_cache_key, True)
                continue
            self.empty_result_cache.delete(empty_cache_key)

            for item in discovered:
                translation = self.watch_repo.add_translation(
                    Translation(
                        anime_id=anime_id,
                        name=canonicalize_translation_name(item.translation_name),
                        translation_type=item.translation_type,
                        language=item.language,
                    )
                )
                self.watch_repo.add_source(
                    WatchSource(
                        anime_id=anime_id,
                        episode=item.episode,
                        translation_id=translation.id or 0,
                        provider_name=item.provider_name,
                        source_name=item.source_name,
                        stream_url=item.stream_url,
                        quality_label=item.quality_label,
                        source_type=item.source_type,
                    )
                )

        return self.watch_repo.get_sources(anime_id=anime_id, episode=episode)

    def _build_title_variants(self, title: str) -> list[str]:
        """Готовит несколько вариантов названия для внешнего поиска."""
        variants = [title.strip()]
        simplified = re.split(r"[:(\\[]", title, maxsplit=1)[0].strip()
        if simplified and simplified not in variants:
            variants.append(simplified)
        normalized = " ".join(title.replace("-", " ").split())
        if normalized and normalized not in variants:
            variants.append(normalized)
        return [item for item in variants if item]

    def _discover_sources(
        self,
        provider: WatchSourceProvider,
        title_variants: list[str],
        episode: int,
        year: int | None,
    ) -> list[DiscoveredWatchSource]:
        """Ищет источники по нескольким вариантам названия и объединяет результат."""
        discovered: list[DiscoveredWatchSource] = []
        seen: set[tuple[str, str, str, str, str]] = set()
        for title_variant in title_variants:
            variant_sources = provider.search_sources(
                title=title_variant,
                episode=episode,
                year=year,
            )
            for item in variant_sources:
                dedupe_key = (
                    canonicalize_translation_name(item.translation_name),
                    str(item.quality_label).strip().lower(),
                    str(item.stream_url).strip(),
                    str(item.provider_name).strip().lower(),
                    str(item.source_name).strip().lower(),
                )
                if dedupe_key in seen:
                    continue
                seen.add(dedupe_key)
                discovered.append(item)
        return sorted(
            discovered,
            key=lambda item: (
                get_translation_priority(item.translation_name),
                -self._quality_rank(item.quality_label),
                item.provider_name.lower(),
                item.source_name.lower(),
            ),
        )

    def _quality_rank(self, value: str | None) -> int:
        """Преобразует метку качества в число для сортировки по убыванию."""
        digits = "".join(
            character for character in str(value or "") if character.isdigit()
        )
        return int(digits) if digits else 0
