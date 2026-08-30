import asyncio
import logging
import re

from backend.application.interface.repositories.watch_repository import WatchRepository
from backend.application.interface.services import (
    WatchSourceProviderInterface as WatchSourceProvider,
)
from backend.domain import Translation, WatchSource
from backend.domain.entities.anime.anime import Anime
from backend.domain.exceptions import ExternalServiceError
from backend.domain.policies.watch_policy import (
    canonicalize_translation_name,
    get_translation_priority,
)
from backend.domain.value_objects.watch.discovery import DiscoveredWatchSource
from backend.domain.value_objects.watch.translation_availability import (
    TranslationEpisodeAvailability,
)
from backend.utils.ttl_cache import TTLCache

logger = logging.getLogger(__name__)

_ADULT_GENRE_MARKERS = ("hentai", "ecchi", "adult", "эрот", "sex", "nsfw")
_ADULT_PROVIDER_NAMES = frozenset({"eporner"})


class WatchSourceSyncService:
    """Синхронизирует источники просмотра из внешнего провайдера в локальное хранилище."""

    def __init__(self, watch_repo: WatchRepository, providers: list[WatchSourceProvider]):
        self.watch_repo = watch_repo
        self.providers = providers
        self.empty_result_cache = TTLCache[
            tuple[str, int, int, int | None, int | None, tuple[str, ...]],
            bool,
        ](
            ttl_seconds=600,
            max_entries=512,
        )
        self._availability_cache = TTLCache[
            tuple[str, int, int],
            list[TranslationEpisodeAvailability],
        ](
            ttl_seconds=1800,
            max_entries=256,
        )

    async def is_enabled(self) -> bool:
        for provider in self.providers:
            if await provider.is_enabled():
                return True
        return False

    @staticmethod
    def _is_adult(genres: list[str] | None) -> bool:
        """Определяет, относится ли тайтл ко взрослому (hentai) контенту по жанрам.

        Args:
            genres: Список жанров тайтла.

        Returns:
            bool: True для hentai/ecchi/эроt-жанров.
        """
        joined = " ".join(genres or []).lower()
        return any(marker in joined for marker in _ADULT_GENRE_MARKERS)

    def _filtered_providers(self, adult: bool) -> list[WatchSourceProvider]:
        """Возвращает список провайдеров для опроса с учётом контента.

        Для взрослого контента остаются только профильные провайдеры
        (Eporner), чтобы не тратить запросы на обычные кинотеки,
        где хентай отсутствует. Для остального — полный список.

        Args:
            adult: True, если тайтл взрослый (hentai).

        Returns:
            list[WatchSourceProvider]: Провайдеры для опроса.
        """
        if not adult:
            return list(self.providers)
        return [
            provider
            for provider in self.providers
            if provider.provider_name.strip().lower() in _ADULT_PROVIDER_NAMES
        ]

    async def get_translations_availability(
        self,
        title: str,
        year: int | None = None,
        shikimori_id: int | None = None,
        genres: list[str] | None = None,
    ) -> list[TranslationEpisodeAvailability]:
        """Возвращает карту доступности серий по озвучкам с TTL-кэшем.

        Результат кэшируется на 30 минут (онгоинги обновляются достаточно
        часто, но не чаще раза в полчаса), ключ включает shikimori_id, чтобы
        строгая адресация не смешивалась с текстовым поиском.

        Args:
            title: Название тайтла.
            year: Год выпуска для смягчённой сверки.
            shikimori_id: Внешний id тайтла (MAL/Shikimori) для строгой адресации.
            genres: Жанры тайтла. Для взрослого (hentai) контента опрашиваются
                только профильные провайдеры (Eporner, Hanime), а не весь список.

        Returns:
            list[TranslationEpisodeAvailability]: Карта доступности серий
            по озвучкам; пустой список, если ни один провайдер не умеет.
        """
        cache_key = (
            str(title).strip().lower(),
            int(year) if year else 0,
            int(shikimori_id) if shikimori_id else 0,
        )
        cached = await self._availability_cache.get(cache_key)
        if cached is not None:
            return list(cached)

        availability: list[TranslationEpisodeAvailability] = []
        for provider in self._filtered_providers(self._is_adult(genres)):
            if not await provider.is_enabled():
                continue
            try:
                availability = await provider.get_translations_availability(
                    title=title,
                    year=year,
                    shikimori_id=shikimori_id,
                )
            except ExternalServiceError:
                logger.warning(
                    "Translation availability provider failed",
                    extra={"provider": provider.provider_name},
                )
                continue
            if availability:
                break
        await self._availability_cache.set(cache_key, availability)
        return availability

    async def get_enabled_provider_names(self) -> list[str]:
        return [
            provider.provider_name for provider in self.providers if await provider.is_enabled()
        ]

    async def get_provider_label(self) -> str | None:
        enabled = await self.get_enabled_provider_names()
        return ", ".join(enabled) if enabled else None

    async def sync_for_anime(
        self,
        anime_id: int,
        anime: Anime | None,
        episode: int,
        force: bool = False,
    ) -> list[WatchSource]:
        """Подтягивает и сохраняет источники для конкретного аниме и эпизода."""
        existing = await self.watch_repo.get_sources(anime_id=anime_id, episode=episode)
        if not anime or not anime.title or not await self.is_enabled():
            return existing

        adult = self._is_adult(getattr(anime, "genres", None))
        existing_provider_names = {str(source.provider_name).strip().lower() for source in existing}
        providers_to_query = [
            provider
            for provider in self._filtered_providers(adult)
            if await provider.is_enabled()
            and (force or provider.provider_name.strip().lower() not in existing_provider_names)
        ]
        if not providers_to_query:
            return existing

        title_variants = await self._build_title_variants(anime.title)
        shikimori_id = self._shikimori_id(anime)
        pending_discoveries: list[
            tuple[tuple[str, int, int, int | None, int | None, tuple[str, ...]], object]
        ] = []
        for provider in providers_to_query:
            empty_cache_key = (
                provider.provider_name.strip().lower(),
                int(anime_id),
                int(episode),
                anime.year,
                shikimori_id,
                tuple(title_variants),
            )
            if not force and await self.empty_result_cache.contains(empty_cache_key):
                continue
            pending_discoveries.append((empty_cache_key, provider))

        if not pending_discoveries:
            return existing

        discovered_batches = await asyncio.gather(
            *[
                self._discover_sources(
                    provider=provider,
                    title_variants=title_variants,
                    episode=episode,
                    year=anime.year,
                    shikimori_id=shikimori_id,
                )
                for _empty_cache_key, provider in pending_discoveries
            ]
        )

        translation_cache: dict[tuple[str, str, str | None], Translation] = {}
        stored_quality_seen: set[tuple[str, str, str | None, str]] = set()
        for (empty_cache_key, _provider), discovered in zip(
            pending_discoveries,
            discovered_batches,
        ):
            if not discovered:
                await self.empty_result_cache.set(empty_cache_key, True)
                continue
            await self.empty_result_cache.delete(empty_cache_key)

            for item in discovered:
                translation_key = (
                    canonicalize_translation_name(item.translation_name),
                    item.translation_type,
                    item.language,
                )
                quality_key = (
                    translation_key[0],
                    translation_key[1],
                    translation_key[2],
                    str(item.quality_label or "").strip().lower(),
                )
                if quality_key in stored_quality_seen:
                    continue
                stored_quality_seen.add(quality_key)
                translation = translation_cache.get(translation_key)
                if translation is None:
                    translation = await self.watch_repo.add_translation(
                        Translation(
                            anime_id=anime_id,
                            name=translation_key[0],
                            translation_type=translation_key[1],
                            language=translation_key[2],
                        )
                    )
                    translation_cache[translation_key] = translation
                await self.watch_repo.add_source(
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

        return await self.watch_repo.get_sources(anime_id=anime_id, episode=episode)

    async def _build_title_variants(self, title: str) -> list[str]:
        """Готовит несколько вариантов названия для внешнего поиска."""
        variants = [title.strip()]
        simplified = re.split(r"[:(\\[]", title, maxsplit=1)[0].strip()
        if simplified and simplified not in variants:
            variants.append(simplified)
        normalized = " ".join(title.replace("-", " ").split())
        if normalized and normalized not in variants:
            variants.append(normalized)

        seasonless = re.sub(
            r"\b(?:season|сезон)\s*\d+\b|\bs\d+\b",
            "",
            normalized,
            flags=re.IGNORECASE,
        )
        seasonless = re.sub(r"\s+", " ", seasonless).strip()
        if seasonless and seasonless != normalized and seasonless not in variants:
            variants.append(seasonless)
        return [item for item in variants if item]

    async def _discover_sources(
        self,
        provider: WatchSourceProvider,
        title_variants: list[str],
        episode: int,
        year: int | None,
        shikimori_id: int | None = None,
    ) -> list[DiscoveredWatchSource]:
        """Ищет источники по нескольким вариантам названия и объединяет результат."""
        discovered: list[DiscoveredWatchSource] = []
        seen: set[tuple[str, str, str, str, str]] = set()
        for title_variant in title_variants:
            try:
                variant_sources = await provider.search_sources(
                    title=title_variant,
                    episode=episode,
                    year=year,
                    shikimori_id=shikimori_id,
                )
            except ExternalServiceError:
                logger.warning(
                    "Watch source provider failed",
                    extra={
                        "provider": provider.provider_name,
                        "episode": episode,
                    },
                )
                continue
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
        ranked_items = [
            (
                item,
                await self._quality_rank(item.quality_label),
                get_translation_priority(item.translation_name),
            )
            for item in discovered
        ]
        return [
            item
            for item, _rank, _priority in sorted(
                ranked_items,
                key=lambda pair: (
                    pair[2],
                    -pair[1],
                    pair[0].provider_name.lower(),
                    pair[0].source_name.lower(),
                ),
            )
        ]

    async def _quality_rank(self, value: str | None) -> int:
        """Преобразует метку качества в число для сортировки по убыванию."""
        digits = "".join(character for character in str(value or "") if character.isdigit())
        return int(digits) if digits else 0

    @staticmethod
    def _shikimori_id(anime) -> int | None:
        """Извлекает shikimori_id (MAL-id) из external_id, если это число.

        Args:
            anime: Сущность Anime.

        Returns:
            int | None: MAL-id или None, если external_id не числовой
            (например, AniList-id) — тогда строгая адресация невозможна.
        """
        external_id = str(getattr(anime, "external_id", "") or "").strip()
        if not external_id.isdigit():
            return None
        return int(external_id)
