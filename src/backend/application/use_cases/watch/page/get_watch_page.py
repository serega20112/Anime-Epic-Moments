"""Сценарий сборки страницы просмотра аниме.

Сценарий оркестрирует источники, прогресс, хайлайты и рейтинг пользователя.
Чистые правила (доступные серии, счётчики озвучек, приоритет источников) живут
в :mod:`episode_plan`.
"""

from __future__ import annotations

import asyncio
from collections.abc import Sequence
from dataclasses import dataclass

from backend.application.dto import WatchPageQuery
from backend.application.interface.repositories.highlight_repository import HighlightRepository
from backend.application.interface.repositories.rating_repository import RatingRepository
from backend.application.interface.repositories.watch_repository import WatchRepository
from backend.application.interface.services import (
    AnimeApiClientInterface,
    WatchSourceSyncServiceInterface,
)
from backend.application.interface.unit_of_work import UnitOfWorkInterface
from backend.application.use_cases.watch.page.episode_plan import (
    available_episodes,
    build_episode_options,
    build_translation_counts,
    dedupe_by_quality,
    format_timestamp,
    resolve_episode_total,
)
from backend.domain import Highlight, Translation, UserAnimeStatus, ViewingSession, WatchSource
from backend.domain.entities.anime.anime import Anime
from backend.domain.policies.watch_policy import (
    get_translation_priority,
    quality_rank,
    source_type_priority,
)
from backend.domain.value_objects.watch.page_data import (
    WatchHighlightCard,
    WatchPageData,
    WatchSourceCard,
)


@dataclass(frozen=True, slots=True)
class _WatchPageState:
    """Данные страницы, прочитанные из базы за одну транзакцию.

    Attributes:
        session: Последняя сессия просмотра зрителя в этой серии.
        status: Статус просмотра тайтла зрителем.
        user_rating: Оценка зрителя этому тайтлу.
        highlights: Хайлайты запрошенной серии.
        highlight_contexts: Контексты плеера по идентификаторам хайлайтов.
    """

    session: ViewingSession | None
    status: UserAnimeStatus | None
    user_rating: int | None
    highlights: list[Highlight]
    highlight_contexts: dict[int, object]


class GetWatchPageUseCase:
    """Собирает данные для страницы просмотра аниме."""

    def __init__(
        self,
        unit_of_work: UnitOfWorkInterface,
        anime_api_client: AnimeApiClientInterface,
        watch_source_sync_service: WatchSourceSyncServiceInterface,
    ) -> None:
        """Инициализирует сценарий страницы просмотра.

        Args:
            unit_of_work: Граница транзакции чтения локальных данных.
            anime_api_client: Клиент каталога для карточки тайтла.
            watch_source_sync_service: Сервис синхронизации источников.
        """
        self._unit_of_work = unit_of_work
        self._anime_api_client = anime_api_client
        self._watch_source_sync_service = watch_source_sync_service

    async def execute(self, query: WatchPageQuery) -> WatchPageData:
        """Собирает страницу просмотра.

        Прогресс, статус, оценка и хайлайты читаются одной короткой транзакцией
        до обращений к внешним провайдерам: соединение с базой не должно висеть
        всё время поиска источников, которое занимает секунды. Синхронизация
        источников и перечитывание озвучек идут в своей транзакции: сервис
        создаёт дорожки и источники прямо во время поиска, и без общего
        контекста эти записи остались бы незафиксированными, а карточки
        источников получили бы ``Unknown`` вместо названия озвучки.

        Args:
            query: Идентификаторы аниме и зрителя, серия, источник и сортировка.

        Returns:
            WatchPageData: Данные страницы просмотра.
        """
        state = await self._load_state(query)
        anime = await self._anime_api_client.get_by_id(query.anime_id)
        (
            sources,
            translations,
            can_discover_sources,
            discovery_provider_name,
        ) = await self._sync_sources(query, anime)
        ranked_sources = dedupe_by_quality(self._rank_sources(sources, translations))
        source_cards = [self._build_source_card(item, translations) for item in ranked_sources]
        active_source_id = (
            query.selected_source_id
            or (state.session.watch_source_id if state.session else None)
            or (ranked_sources[0].id if ranked_sources else None)
        )
        active_source = next((item for item in ranked_sources if item.id == active_source_id), None)
        availability = await self._watch_source_sync_service.get_translations_availability(
            title=(anime.title if anime else ""),
            year=(anime.year if anime else None),
            shikimori_id=(anime.mal_id if anime else None),
            genres=(anime.genres if anime else None),
        )
        if not isinstance(availability, list):
            availability = []
        active_translation_name = (
            translations[active_source.translation_id].name
            if active_source and active_source.translation_id in translations
            else None
        )
        episodes = available_episodes(
            availability=availability,
            active_translation_name=active_translation_name,
            sources=source_cards,
        )
        episode_total = resolve_episode_total(
            available_episodes_list=episodes,
            episode=query.episode,
            fallback_total=anime.episode_count if anime and anime.episode_count else None,
        )

        return WatchPageData(
            anime_id=query.anime_id,
            anime_title=anime.title if anime and anime.title else f"Anime #{query.anime_id}",
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
            episode_options=build_episode_options(
                total=episode_total,
                current_episode=query.episode,
                available_episodes_list=episodes,
            ),
            translation_episode_counts=build_translation_counts(
                availability=availability,
                source_cards=source_cards,
                translations=translations,
                active_translation_name=active_translation_name,
            ),
            selected_source_id=active_source.id if active_source else None,
            selected_translation_id=(active_source.translation_id if active_source else None),
            sources=source_cards,
            highlights=self._build_highlight_cards(state, translations, source_cards, anime),
            current_status=state.status.status if state.status else None,
            last_position_seconds=state.session.position_seconds if state.session else 0.0,
            preferred_start_seconds=max(float(query.preferred_start_seconds or 0.0), 0.0),
            saved_volume=state.session.volume if state.session else 1.0,
            saved_quality_label=(
                state.session.quality_label
                if state.session
                else (active_source.quality_label if active_source else None)
            ),
            can_discover_sources=can_discover_sources,
            discovery_provider_name=discovery_provider_name,
            user_rating=state.user_rating,
        )

    async def _sync_sources(
        self,
        query: WatchPageQuery,
        anime: Anime | None,
    ) -> tuple[list[WatchSource], dict[int, Translation], bool, str | None]:
        """Синхронизировать источники и прочитать озвучки одной транзакцией.

        Args:
            query: Идентификаторы аниме и зрителя, номер серии.
            anime: Карточка тайтла из каталога либо None.

        Returns:
            tuple: Источники серии, озвучки по id, признак доступности
            обнаружения и подпись провайдеров.
        """
        async with self._unit_of_work as uow:
            sources, can_discover_sources, provider_label = await asyncio.gather(
                self._watch_source_sync_service.sync_for_anime(
                    unit_of_work=uow,
                    anime_id=query.anime_id,
                    anime=anime,
                    episode=query.episode,
                ),
                self._watch_source_sync_service.is_enabled(),
                self._watch_source_sync_service.get_provider_label(),
            )
            local_translations = await uow.repository(WatchRepository).get_translations(
                anime_id=query.anime_id
            )
        translations_by_id = {item.id: item for item in local_translations}
        return sources, translations_by_id, can_discover_sources, provider_label

    async def _load_state(self, query: WatchPageQuery) -> _WatchPageState:
        """Прочитать локальные данные страницы одной транзакцией.

        Args:
            query: Идентификаторы аниме и зрителя, номер серии.

        Returns:
            _WatchPageState: Прогресс, статус, оценка, хайлайты и контексты.
        """
        async with self._unit_of_work as uow:
            watch_repository = uow.repository(WatchRepository)
            highlight_repository = uow.repository(HighlightRepository)
            session = (
                await watch_repository.get_session(
                    user_id=query.user_id, anime_id=query.anime_id, episode=query.episode
                )
                if query.user_id
                else None
            )
            status = (
                await watch_repository.get_status(user_id=query.user_id, anime_id=query.anime_id)
                if query.user_id
                else None
            )
            user_rating = (
                await uow.repository(RatingRepository).get_user_rating(
                    user_id=query.user_id, anime_id=query.anime_id
                )
                if query.user_id
                else None
            )
            highlights = await highlight_repository.get_by_anime_episode(
                anime_id=query.anime_id,
                episode=query.episode,
            )
            contexts = await watch_repository.get_highlight_contexts(
                [highlight.id for highlight in highlights if highlight.id is not None]
            )
        return _WatchPageState(
            session=session,
            status=status,
            user_rating=user_rating,
            highlights=highlights,
            highlight_contexts={item.highlight_id: item for item in contexts},
        )

    def _build_source_card(
        self,
        item: WatchSource,
        translations: dict[int, Translation],
    ) -> WatchSourceCard:
        """Собрать карточку источника просмотра.

        Args:
            item: Источник, найденный сервисом синхронизации.
            translations: Локальные дорожки тайтла по id.

        Returns:
            WatchSourceCard: Карточка для шаблона и выбора варианта по умолчанию.
        """
        return WatchSourceCard(
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

    def _build_highlight_cards(
        self,
        state: _WatchPageState,
        translations: dict[int, Translation],
        source_cards: list[WatchSourceCard],
        anime: Anime | None,
    ) -> list[WatchHighlightCard]:
        """Собрать карточки хайлайтов серии с привязкой к озвучке и провайдеру.

        Args:
            state: Прочитанные из базы данные страницы.
            translations: Локальные дорожки тайтла по id.
            source_cards: Карточки источников в порядке приоритета.
            anime: Карточка тайтла из каталога либо None.

        Returns:
            list[WatchHighlightCard]: Карточки хайлайтов для панели серии.
        """
        source_by_id = {item.source_id: item for item in source_cards}
        cards: list[WatchHighlightCard] = []
        for item in state.highlights:
            context = state.highlight_contexts.get(item.id)
            translation_name = None
            provider_name = None
            if context:
                translation = translations.get(context.translation_id)
                translation_name = translation.name if translation else None
                source = source_by_id.get(context.watch_source_id)
                provider_name = source.provider_name if source else None
            cards.append(
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
                    start_timestamp=format_timestamp(item.start_timestamp),
                    end_timestamp=format_timestamp(item.end_timestamp),
                    emotion=item.emotion,
                    is_spoiler=item.is_spoiler,
                    translation_name=translation_name,
                    provider_name=provider_name,
                )
            )
        return cards

    @staticmethod
    def _rank_sources(
        sources: Sequence[WatchSource],
        translations: dict[int, Translation],
    ) -> list[WatchSource]:
        """Сортирует источники по типу, озвучке, качеству и провайдеру.

        Порядок задаёт вариант по умолчанию: сначала прямые потоки, затем
        приоритетные озвучки, затем лучшее качество.

        Args:
            sources: Источники, найденные сервисом синхронизации.
            translations: Локальные дорожки тайтла по id.

        Returns:
            list[WatchSource]: Источники в порядке приоритета.
        """
        keyed = []
        for item in sources:
            keyed.append(
                (
                    source_type_priority(item.source_type),
                    get_translation_priority(
                        translations[item.translation_id].name
                        if item.translation_id in translations
                        else ""
                    ),
                    -quality_rank(item.quality_label),
                    item.provider_name.lower(),
                    item,
                )
            )
        keyed.sort(key=lambda pair: pair[:4])
        return [pair[4] for pair in keyed]
