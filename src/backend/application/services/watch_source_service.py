"""Сервис синхронизации источников просмотра из внешних провайдеров."""

import asyncio
import logging
import re

from backend.application.interface.repositories.watch_repository import WatchRepository
from backend.application.interface.services import (
    TTLCacheInterface,
    WatchSourceProviderInterface,
    WatchSourceSyncServiceInterface,
)
from backend.application.interface.unit_of_work import UnitOfWorkInterface
from backend.domain import Translation, WatchSource
from backend.domain.entities.anime.anime import Anime, has_adult_genres
from backend.domain.exceptions import ExternalServiceError
from backend.domain.policies.watch_policy import (
    canonicalize_translation_name,
    get_translation_priority,
    quality_rank,
)
from backend.domain.value_objects.watch.discovery import DiscoveredWatchSource
from backend.domain.value_objects.watch.translation_availability import (
    TranslationEpisodeAvailability,
)

logger = logging.getLogger("anime_epic_moments")

_ADULT_PROVIDER_NAMES = frozenset({"eporner", "hentaigasm", "hanime"})


class WatchSourceSyncService(WatchSourceSyncServiceInterface):
    """Синхронизирует источники просмотра из внешнего провайдера в локальное хранилище.

    Кэши приходят извне и живут дольше запроса: сервис собирается в DI со
    scope=REQUEST, поэтому собственные кэши пересоздавались бы на каждый
    HTTP-запрос, и ни один TTL никогда не наступил бы.

    Собственного репозитория у сервиса нет: запись идёт через единицу работы
    вызывающего сценария, иначе накопленные изменения остались бы незафиксированными.
    """

    def __init__(
        self,
        providers: list[WatchSourceProviderInterface],
        empty_result_cache: TTLCacheInterface,
        availability_cache: TTLCacheInterface,
    ) -> None:
        """Инициализирует сервис синхронизации источников.

        Args:
            providers: Список провайдеров источников.
            empty_result_cache: Кэш отметок «источников нет».
            availability_cache: Кэш карты доступности серий по озвучкам.
        """
        self.providers = providers
        self.empty_result_cache = empty_result_cache
        self._availability_cache = availability_cache

    async def is_enabled(self) -> bool:
        """Проверить, включён ли провайдер в настройках."""
        for provider in self.providers:
            if await provider.is_enabled():
                return True
        return False

    def _filtered_providers(self, adult: bool) -> list[WatchSourceProviderInterface]:
        """Возвращает список провайдеров для опроса с учётом контента.

        Для взрослого контента остаются только профильные провайдеры
        (Eporner, Hentaigasm, Hanime), чтобы не тратить запросы на
        обычные кинотеки, где хентай отсутствует. Для остального — полный
        список. Kodik в список взрослых намеренно не входит: его каталог
        выдаёт хентай-тайтлы как «не-озвучки» (оригинал и спец-серии), и
        текстовый поиск по названию постоянно цепляет их и засоряет выдачу.

        Args:
            adult: True, если тайтл взрослый (hentai).

        Returns:
            list[WatchSourceProviderInterface]: Провайдеры для опроса.
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
                только профильные провайдеры (Eporner, Hentaigasm, Hanime),
                а не весь список.

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
        for provider in self._filtered_providers(has_adult_genres(genres)):
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
        """Получить имена включённых провайдеров."""
        return [
            provider.provider_name for provider in self.providers if await provider.is_enabled()
        ]

    async def get_provider_label(self) -> str | None:
        """Собрать подпись провайдеров для интерфейса."""
        enabled = await self.get_enabled_provider_names()
        return ", ".join(enabled) if enabled else None

    async def sync_for_anime(
        self,
        unit_of_work: UnitOfWorkInterface,
        anime_id: int,
        anime: Anime | None,
        episode: int,
        force: bool = False,
    ) -> list[WatchSource]:
        """Подтягивает и сохраняет источники для конкретного аниме и эпизода.

        Args:
            unit_of_work: Граница транзакции вызывающего сценария.
            anime_id: Идентификатор тайтла в локальном каталоге.
            anime: Карточка тайтла из каталога либо None.
            episode: Номер серии.
            force: Признак принудительного опроса, сбрасывающего кэш отметок.

        Returns:
            list[WatchSource]: Источники серии после синхронизации.
        """
        watch_repository = unit_of_work.repository(WatchRepository)
        existing = await watch_repository.get_sources(anime_id=anime_id, episode=episode)
        if not anime or not anime.title or not await self.is_enabled():
            return existing

        adult = anime.is_adult
        providers_to_query = await self._select_providers(existing, adult=adult, force=force)
        if not providers_to_query:
            return existing

        logger.info(
            "Watch source sync started",
            extra={
                "anime_id": anime_id,
                "title": anime.title,
                "episode": episode,
                "adult": adult,
                "genres": list(anime.genres or []),
                "queried": [provider.provider_name for provider in providers_to_query],
                "already_stored": sorted(
                    str(source.provider_name).strip().lower() for source in existing
                ),
            },
        )

        title_variants = await self._build_title_variants(anime.title)
        shikimori_id = anime.mal_id
        pending_discoveries = await self._plan_discoveries(
            providers_to_query,
            anime_id=anime_id,
            episode=episode,
            year=anime.year,
            shikimori_id=shikimori_id,
            title_variants=title_variants,
            force=force,
        )
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
        await self._store_discoveries(
            watch_repository,
            pending_discoveries,
            discovered_batches,
            anime_id=anime_id,
            episode=episode,
        )
        return await watch_repository.get_sources(anime_id=anime_id, episode=episode)

    async def _select_providers(
        self,
        existing: list[WatchSource],
        *,
        adult: bool,
        force: bool,
    ) -> list[WatchSourceProviderInterface]:
        """Отобирает провайдеры, которые нужно опросить в этом цикле синхронизации.

        Args:
            existing: Уже сохранённые источники серии.
            adult: True для взрослого (hentai) контента.
            force: Признак принудительного опроса всех включённых провайдеров.

        Returns:
            list[WatchSourceProviderInterface]: Провайдеры для опроса.
        """
        existing_provider_names = {str(source.provider_name).strip().lower() for source in existing}
        return [
            provider
            for provider in self._filtered_providers(adult)
            if await provider.is_enabled()
            and (
                force
                or provider.ephemeral_links
                or provider.provider_name.strip().lower() not in existing_provider_names
            )
        ]

    async def _plan_discoveries(
        self,
        providers: list[WatchSourceProviderInterface],
        *,
        anime_id: int,
        episode: int,
        year: int | None,
        shikimori_id: int | None,
        title_variants: list[str],
        force: bool,
    ) -> list[tuple[tuple[str, int, int, int | None, int | None, tuple[str, ...]], object]]:
        """Формирует список опросов с учётом кэша отметок «источников нет».

        Args:
            providers: Отобранные для опроса провайдеры.
            anime_id: Идентификатор тайтла в локальном каталоге.
            episode: Номер серии.
            year: Год выпуска тайтла.
            shikimori_id: Внешний id тайтла, если он числовой.
            title_variants: Варианты названия для внешнего поиска.
            force: Признак принудительного опроса, игнорирующего кэш.

        Returns:
            list[tuple[...]]: Пары «ключ кэша, провайдер» для параллельного опроса.
        """
        pending: list[
            tuple[tuple[str, int, int, int | None, int | None, tuple[str, ...]], object]
        ] = []
        for provider in providers:
            empty_cache_key = (
                provider.provider_name.strip().lower(),
                int(anime_id),
                int(episode),
                year,
                shikimori_id,
                tuple(title_variants),
            )
            if not force and await self.empty_result_cache.contains(empty_cache_key):
                continue
            pending.append((empty_cache_key, provider))
        return pending

    async def _store_discoveries(
        self,
        watch_repository: WatchRepository,
        pending_discoveries: list[
            tuple[tuple[str, int, int, int | None, int | None, tuple[str, ...]], object]
        ],
        discovered_batches: list[list[DiscoveredWatchSource]],
        *,
        anime_id: int,
        episode: int,
    ) -> None:
        """Сохраняет найденные источники и озвучки в транзакции вызывающего сценария.

        Args:
            watch_repository: Репозиторий просмотра внутри единицы работы.
            pending_discoveries: Планирование опросов «ключ кэша, провайдер».
            discovered_batches: Результаты опросов в том же порядке.
            anime_id: Идентификатор тайтла в локальном каталоге.
            episode: Номер серии, для которой ищутся источники.
        """
        translation_cache: dict[tuple[str, str, str | None], Translation] = {}
        stored_quality_seen: set[tuple[str, str, str | None, str, str]] = set()
        for (empty_cache_key, _provider), discovered in zip(
            pending_discoveries,
            discovered_batches,
        ):
            logger.info(
                "Watch source provider returned",
                extra={
                    "anime_id": anime_id,
                    "episode": episode,
                    "provider": _provider.provider_name,
                    "discovered": len(discovered),
                },
            )
            if not discovered:
                await self.empty_result_cache.set(empty_cache_key, True)
                continue
            await self.empty_result_cache.delete(empty_cache_key)

            if _provider.ephemeral_links:
                await watch_repository.delete_sources_by_provider(
                    anime_id=anime_id,
                    provider_name=_provider.provider_name,
                    episode=episode,
                )

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
                    str(item.source_name or "").strip().lower(),
                )
                if quality_key in stored_quality_seen:
                    continue
                stored_quality_seen.add(quality_key)
                translation = translation_cache.get(translation_key)
                if translation is None:
                    translation = await watch_repository.add_translation(
                        Translation(
                            anime_id=anime_id,
                            name=translation_key[0],
                            translation_type=translation_key[1],
                            language=translation_key[2],
                        )
                    )
                    translation_cache[translation_key] = translation
                await watch_repository.add_source(
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
        provider: WatchSourceProviderInterface,
        title_variants: list[str],
        episode: int,
        year: int | None,
        shikimori_id: int | None = None,
    ) -> list[DiscoveredWatchSource]:
        """Ищет источники по нескольким вариантам названия и объединяет результат.

        Варианты опрашиваются параллельно: каждый — отдельный сетевой запрос,
        а у Hentaigasm/Eporner поиск занимает 2–4 с, поэтому последовательный
        обход удваивал время ожидания страницы просмотра.

        Args:
            provider: Провайдер внешних источников.
            title_variants: Варианты названия для поиска.
            episode: Номер серии.
            year: Год выпуска для смягчённой сверки.
            shikimori_id: Внешний id тайтла (MAL/Shikimori), если известен.

        Returns:
            list[DiscoveredWatchSource]: Объединённый и отсортированный список.
        """

        async def search_variant(title_variant: str) -> list[DiscoveredWatchSource]:
            """Найти источники по одному варианту названия."""
            try:
                return await provider.search_sources(
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
                        "title_variant": title_variant,
                    },
                )
                return []

        batches = await asyncio.gather(*(search_variant(item) for item in title_variants))

        discovered: list[DiscoveredWatchSource] = []
        seen: set[tuple[str, str, str, str, str]] = set()
        for variant_sources in batches:
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
                quality_rank(item.quality_label),
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
