import asyncio

from src.backend.domain.watch.policy import get_translation_priority
from src.backend.domain.watch.value_object import (
    WatchHighlightCard,
    WatchPageData,
    WatchSourceCard,
)
from src.backend.infrastructure.external.anime_api_client import AnimeApiClient
from src.backend.repository.highlight_repository import HighlightRepository
from src.backend.repository.watch_repository import WatchRepository
from src.backend.services.watch_source_sync_service import WatchSourceSyncService


class GetWatchPageUseCase:
    """Собирает данные для страницы просмотра аниме."""

    def __init__(
        self,
        watch_repo: WatchRepository,
        highlight_repo: HighlightRepository,
        anime_api_client: AnimeApiClient,
        watch_source_sync_service: WatchSourceSyncService,
    ):
        self.watch_repo = watch_repo
        self.highlight_repo = highlight_repo
        self.anime_api_client = anime_api_client
        self.watch_source_sync_service = watch_source_sync_service

    async def execute(
        self,
        anime_id: int,
        episode: int,
        user_id: int | None = None,
        selected_source_id: int | None = None,
        preferred_start_seconds: float | None = None,
    ) -> WatchPageData:
        anime = await self.anime_api_client.get_by_id(anime_id)
        sources = await self.watch_source_sync_service.sync_for_anime(
            anime_id=anime_id,
            anime=anime,
            episode=episode,
        )
        translations = {
            item.id: item
            for item in await self.watch_repo.get_translations(anime_id=anime_id)
        }
        sources = sorted(
            sources,
            key=lambda item: (
                self._source_type_priority(item.source_type),
                get_translation_priority(
                    translations[item.translation_id].name
                    if item.translation_id in translations
                    else ""
                ),
                -self._quality_rank(item.quality_label),
                item.provider_name.lower(),
            ),
        )
        session = (
            await self.watch_repo.get_session(
                user_id=user_id, anime_id=anime_id, episode=episode
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
            selected_source_id
            or (session.watch_source_id if session else None)
            or (sources[0].id if sources else None)
        )
        active_source = next(
            (item for item in sources if item.id == active_source_id), None
        )
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
            episode=episode,
        )
        highlight_contexts = {
            item.highlight_id: item
            for item in await self.watch_repo.get_highlight_contexts(
                [
                    highlight.id
                    for highlight in episode_highlights
                    if highlight.id is not None
                ]
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
                    start_timestamp=self._format_timestamp(item.start_timestamp),
                    end_timestamp=self._format_timestamp(item.end_timestamp),
                    emotion=item.emotion,
                    is_spoiler=item.is_spoiler,
                    translation_name=translation_name,
                    provider_name=provider_name,
                )
            )

        episode_total = self._resolve_episode_total(
            anime=anime,
            sources=source_cards,
            episode=episode,
        )
        can_discover_sources, discovery_provider_name = await asyncio.gather(
            self.watch_source_sync_service.is_enabled(),
            self.watch_source_sync_service.get_provider_label(),
        )

        return WatchPageData(
            anime_id=anime_id,
            anime_title=anime.title if anime and anime.title else f"Anime #{anime_id}",
            anime_cover=anime.cover_url if anime else None,
            anime_description=(
                anime.description
                if anime and anime.description
                else "Описание недоступно"
            ),
            anime_year=anime.year if anime else None,
            anime_rating=anime.rating if anime else None,
            genres=anime.genres if anime and anime.genres else [],
            episode=episode,
            episode_total=episode_total,
            episode_options=self._build_episode_options(
                total=episode_total,
                current_episode=episode,
            ),
            selected_source_id=active_source.id if active_source else None,
            selected_translation_id=(
                active_source.translation_id if active_source else None
            ),
            sources=source_cards,
            highlights=highlight_cards,
            current_status=status.status if status else None,
            last_position_seconds=session.position_seconds if session else 0.0,
            preferred_start_seconds=max(float(preferred_start_seconds or 0.0), 0.0),
            saved_volume=session.volume if session else 1.0,
            saved_quality_label=(
                session.quality_label
                if session
                else (active_source.quality_label if active_source else None)
            ),
            can_discover_sources=can_discover_sources,
            discovery_provider_name=discovery_provider_name,
        )

    def _format_timestamp(self, seconds: float) -> str:
        minutes = int(seconds // 60)
        sec = int(seconds % 60)
        return f"{minutes:02d}:{sec:02d}"

    def _quality_rank(self, value: str | None) -> int:
        """Преобразует строку качества в числовой ранг для сортировки."""
        digits = "".join(
            character for character in str(value or "") if character.isdigit()
        )
        return int(digits) if digits else 0

    def _source_type_priority(self, value: str | None) -> int:
        """Возвращает приоритет типа источника для выбора дефолтного варианта."""
        priorities = {
            "stream": 0,
            "embed": 1,
            "external": 2,
        }
        return priorities.get(str(value or "").strip().lower(), 3)

    def _resolve_episode_total(self, anime, sources, episode: int) -> int | None:
        """Определяет диапазон эпизодов для episode dropdown."""
        candidates = [max(int(episode), 1)]
        if anime and getattr(anime, "episode_count", None):
            candidates.append(int(anime.episode_count))
        candidates.extend(
            int(item.episode)
            for item in sources
            if getattr(item, "episode", None)
        )
        episode_total = max(candidates) if candidates else 1
        return episode_total if episode_total > 0 else None

    def _build_episode_options(
        self,
        total: int | None,
        current_episode: int,
    ) -> list[int]:
        """Строит список эпизодов для select, если размер диапазона разумный."""
        if total is None:
            return []
        capped_total = max(int(total), int(current_episode), 1)
        if capped_total > 500:
            return []
        return list(range(1, capped_total + 1))
