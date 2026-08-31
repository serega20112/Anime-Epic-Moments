import asyncio

from backend.application.dto import WatchPageQuery
from backend.application.interface.repositories.highlight_repository import HighlightRepository
from backend.application.interface.repositories.watch_repository import WatchRepository
from backend.application.interface.services import AnimeApiClientInterface as AnimeApiClient
from backend.application.interface.services import (
    WatchSourceSyncServiceInterface as WatchSourceSyncService,
)
from backend.application.interface.unit_of_work import UnitOfWorkInterface
from backend.domain.policies.watch_policy import (
    canonicalize_translation_name,
    get_translation_priority,
)
from backend.domain.value_objects.watch.page_data import (
    TranslationEpisodeCount,
    WatchHighlightCard,
    WatchPageData,
    WatchSourceCard,
)


class GetWatchPageUseCase:
    """Собирает данные для страницы просмотра аниме."""

    def __init__(
        self,
        watch_repo: WatchRepository,
        highlight_repo: HighlightRepository,
        anime_api_client: AnimeApiClient,
        watch_source_sync_service: WatchSourceSyncService,
        unit_of_work: UnitOfWorkInterface,
    ):
        self.watch_repo = watch_repo
        self.highlight_repo = highlight_repo
        self.anime_api_client = anime_api_client
        self.watch_source_sync_service = watch_source_sync_service
        self.unit_of_work = unit_of_work

    async def execute(
        self,
        anime_id: int,
        query: WatchPageQuery,
        user_id: int | None = None,
    ) -> WatchPageData:
        """Build the watch page within a transaction."""
        async with self.unit_of_work:
            return await self._execute(anime_id, query, user_id)

    async def _execute(
        self,
        anime_id: int,
        query: WatchPageQuery,
        user_id: int | None = None,
    ) -> WatchPageData:
        anime = await self.anime_api_client.get_by_id(anime_id)
        sources = await self.watch_source_sync_service.sync_for_anime(
            anime_id=anime_id,
            anime=anime,
            episode=query.episode,
        )
        translations = {
            item.id: item for item in await self.watch_repo.get_translations(anime_id=anime_id)
        }
        keyed = []
        for item in sources:
            keyed.append(
                (
                    await self._source_type_priority(item.source_type),
                    get_translation_priority(
                        translations[item.translation_id].name
                        if item.translation_id in translations
                        else ""
                    ),
                    -await self._quality_rank(item.quality_label),
                    item.provider_name.lower(),
                    item,
                )
            )
        keyed.sort(key=lambda pair: pair[:4])
        sources = [pair[4] for pair in keyed]
        sources = await self._dedupe_by_quality(sources)
        session = (
            await self.watch_repo.get_session(
                user_id=user_id, anime_id=anime_id, episode=query.episode
            )
            if user_id
            else None
        )
        status = (
            await self.watch_repo.get_status(user_id=user_id, anime_id=anime_id)
            if user_id
            else None
        )

        active_source_id = (
            query.selected_source_id
            or (session.watch_source_id if session else None)
            or (sources[0].id if sources else None)
        )
        active_source = next((item for item in sources if item.id == active_source_id), None)
        source_cards = [
            WatchSourceCard(
                source_id=item.id or 0,
                translation_id=item.translation_id,
                translation_name=(
                    translations[item.translation_id].name
                    if item.translation_id in translations
                    else "Unknown"
                ),
                episode=item.episode,
                provider_name=item.provider_name,
                source_name=item.source_name,
                quality_label=item.quality_label,
                stream_url=item.stream_url,
                source_type=item.source_type,
            )
            for item in sources
        ]
        source_by_id = {
            item.source_id: item
            for item in source_cards
            if getattr(item, "source_id", None) is not None
        }

        episode_highlights = await self.highlight_repo.get_by_anime_episode(
            anime_id=anime_id,
            episode=query.episode,
        )
        highlight_contexts = {
            item.highlight_id: item
            for item in await self.watch_repo.get_highlight_contexts(
                [highlight.id for highlight in episode_highlights if highlight.id is not None]
            )
        }
        highlight_cards = []
        for item in episode_highlights:
            context = highlight_contexts.get(item.id)
            translation_name = None
            provider_name = None
            if context:
                translation = translations.get(context.translation_id)
                translation_name = translation.name if translation else None
                source = source_by_id.get(context.watch_source_id)
                provider_name = source.provider_name if source else None
            highlight_cards.append(
                WatchHighlightCard(
                    id=item.id or 0,
                    title=(
                        item.title
                        if item.title
                        else (
                            context.title
                            if context and context.title
                            else f"{anime.title if anime else 'Anime'} - серия {item.episode}"
                        )
                    ),
                    category=item.category,
                    likes_count=item.likes_count,
                    description=item.description or "",
                    start_timestamp=await self._format_timestamp(item.start_timestamp),
                    end_timestamp=await self._format_timestamp(item.end_timestamp),
                    emotion=item.emotion,
                    is_spoiler=item.is_spoiler,
                    translation_name=translation_name,
                    provider_name=provider_name,
                )
            )

        availability = await self.watch_source_sync_service.get_translations_availability(
            title=(anime.title if anime else ""),
            year=(anime.year if anime else None),
            shikimori_id=self._shikimori_id(anime),
            genres=(anime.genres if anime else None),
        )
        if not isinstance(availability, list):
            availability = []
        active_translation_name = (
            translations[active_source.translation_id].name
            if active_source and active_source.translation_id in translations
            else None
        )
        per_translation_counts = await self._build_translation_counts(
            availability=availability,
            source_cards=source_cards,
            translations=translations,
            active_translation_name=active_translation_name,
        )
        available_episodes = await self._available_episodes(
            availability=availability,
            active_translation_name=active_translation_name,
            sources=source_cards,
        )
        fallback_total = anime.episode_count if anime and anime.episode_count else None
        episode_total = await self._resolve_episode_total(
            available_episodes=available_episodes,
            episode=query.episode,
            fallback_total=fallback_total,
        )
        can_discover_sources, discovery_provider_name = await asyncio.gather(
            self.watch_source_sync_service.is_enabled(),
            self.watch_source_sync_service.get_provider_label(),
        )

        return WatchPageData(
            anime_id=anime_id,
            anime_title=anime.title if anime and anime.title else f"Anime #{anime_id}",
            anime_title_original=(anime.original_title if anime else None),
            anime_cover=anime.cover_url if anime else None,
            anime_description=(
                anime.description if anime and anime.description else "Описание недоступно"
            ),
            anime_year=anime.year if anime else None,
            anime_rating=anime.rating if anime else None,
            genres=anime.genres if anime and anime.genres else [],
            episode=query.episode,
            episode_total=episode_total,
            episode_options=await self._build_episode_options(
                total=episode_total,
                current_episode=query.episode,
                available_episodes=available_episodes,
            ),
            translation_episode_counts=per_translation_counts,
            selected_source_id=active_source.id if active_source else None,
            selected_translation_id=(active_source.translation_id if active_source else None),
            sources=source_cards,
            highlights=highlight_cards,
            current_status=status.status if status else None,
            last_position_seconds=session.position_seconds if session else 0.0,
            preferred_start_seconds=max(float(query.preferred_start_seconds or 0.0), 0.0),
            saved_volume=session.volume if session else 1.0,
            saved_quality_label=(
                session.quality_label
                if session
                else (active_source.quality_label if active_source else None)
            ),
            can_discover_sources=can_discover_sources,
            discovery_provider_name=discovery_provider_name,
        )

    async def _format_timestamp(self, seconds: float) -> str:
        minutes = int(seconds // 60)
        sec = int(seconds % 60)
        return f"{minutes:02d}:{sec:02d}"

    async def _quality_rank(self, value: str | None) -> int:
        """Преобразует строку качества в числовой ранг для сортировки."""
        digits = "".join(character for character in str(value or "") if character.isdigit())
        return int(digits) if digits else 0

    async def _source_type_priority(self, value: str | None) -> int:
        """Возвращает приоритет типа источника для выбора дефолтного варианта."""
        priorities = {
            "stream": 0,
            "embed": 1,
            "external": 2,
        }
        return priorities.get(str(value or "").strip().lower(), 3)

    async def _dedupe_by_quality(self, sources: list) -> list:
        """Оставляет один источник на озвучку и качество (дубли качества убирает).

        Из-за нескольких релизов одного провайдера в БД может оказаться
        несколько источников с одинаковым качеством (например, «1080, 1080»).
        Здесь оставляем только первый — он лучший по приоритету/сортировке.
        """
        deduped: list = []
        seen: set[tuple[int, str]] = set()
        for item in sources:
            key = (
                int(item.translation_id),
                str(item.quality_label or "").strip().lower(),
            )
            if key in seen:
                continue
            seen.add(key)
            deduped.append(item)
        return deduped

    async def _available_episodes(
        self,
        availability,
        active_translation_name,
        sources,
    ) -> list[int] | None:
        """Возвращает реально доступные серии тайтла или None, если данных нет.

        Приоритет — набор серий озвучки, выбранной в плеере: тогда «фантомные»
        серии чужих студий не показываются. Если выбранная озвучка в карте
        доступности отсутствует — берётся объединение всех озвучек, иначе
        None (fallback на клиентский диапазон).
        """
        if availability and active_translation_name:
            canonical_active = canonicalize_translation_name(active_translation_name)
            for record in availability:
                if (
                    canonicalize_translation_name(record.title) == canonical_active
                    and record.available_episodes
                ):
                    return sorted(set(record.available_episodes))
        if availability:
            merged = sorted({ep for record in availability for ep in record.available_episodes})
            if merged:
                return merged
        return None

    async def _build_translation_counts(
        self,
        availability,
        source_cards,
        translations,
        active_translation_name,
    ) -> list[TranslationEpisodeCount]:
        """Собирает счётчики вышедших серий по озвучкам для UI.

        Счётчик берётся из ответа провайдера по каждой озвучке отдельно,
        а не из метаданных каталога — это исключает «12 серий» там, где
        студия выпустила только 8.
        """
        if not availability:
            return []
        counts: list[TranslationEpisodeCount] = []
        seen_names: set[str] = set()
        for record in availability:
            canonical = canonicalize_translation_name(record.title)
            if canonical in seen_names:
                continue
            seen_names.add(canonical)
            is_active = bool(
                active_translation_name
                and canonicalize_translation_name(active_translation_name) == canonical
            )
            counts.append(
                TranslationEpisodeCount(
                    translation_name=record.title,
                    available_count=int(record.episodes_count),
                    is_active=is_active,
                )
            )
        return counts

    async def _resolve_episode_total(
        self,
        available_episodes: list[int] | None,
        episode: int,
        fallback_total: int | None = None,
    ) -> int | None:
        """Считает общее число серий по фактически доступным.

        Приоритет — реальный набор серий от провайдера (``available_episodes``):
        так «фантомные» серии чужих озвучек не попадают в общий счёт. Если
        карта доступности пуста — используется широтное fallback
        (``fallback_total`` из каталога/источников).

        Args:
            available_episodes: Список реально доступных серий либо None.
            episode: Текущая серия.
            fallback_total: Количество серий из каталога (fallback).

        Returns:
            int | None: Максимум доступных серий либо fallback.
        """
        if available_episodes:
            return max(max(available_episodes), max(int(episode), 1))
        if fallback_total:
            return max(int(fallback_total), max(int(episode), 1))
        return max(int(episode), 1) if episode else None

    async def _build_episode_options(
        self,
        total: int | None,
        current_episode: int,
        available_episodes: list[int] | None = None,
    ) -> list[int]:
        """Строит список эпизодов для select.

        Когда известен реальный набор серий (``available_episodes``) — отдаёт
        только их, чтобы не показывать невышедшие серии. Иначе fallback на
        диапазон 1..total.

        Args:
            total: Общее число серий (fallback).
            current_episode: Текущая серия.
            available_episodes: Реально доступные серии или None.

        Returns:
            list[int]: Возможные для выбора номера серий.
        """
        if available_episodes:
            capped = [ep for ep in sorted(set(available_episodes)) if 1 <= int(ep) <= 500]
            if current_episode not in capped:
                capped.append(int(current_episode))
                capped.sort()
            return capped
        if total is None:
            return []
        capped_total = max(int(total), int(current_episode), 1)
        if capped_total > 500:
            return []
        return list(range(1, capped_total + 1))

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
