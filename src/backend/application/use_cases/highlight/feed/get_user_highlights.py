"""Сценарий личного дашборда хайлайтов пользователя."""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence

from backend.application.dto import HighlightDashboardQuery
from backend.application.interface.repositories.highlight_repository import HighlightRepository
from backend.application.interface.repositories.user_repository import UserRepository
from backend.application.interface.services import AnimeApiClientInterface
from backend.application.interface.unit_of_work import UnitOfWorkInterface
from backend.domain import (
    Highlight,
    HighlightAnimeGroup,
    HighlightCard,
    HighlightDashboard,
    HighlightEngagement,
    HighlightStats,
    User,
)
from backend.domain.clock import utc_now

AnimeMeta = tuple[str, str | None, int, str | None]


class GetUserHighlightsUseCase:
    """Возвращает дашборд хайлайтов пользователя с фильтрами и статистикой."""

    def __init__(
        self,
        unit_of_work: UnitOfWorkInterface,
        anime_api_client: AnimeApiClientInterface,
    ) -> None:
        """Собрать сценарий дашборда хайлайтов.

        Args:
            unit_of_work: Граница транзакции для чтения хайлайтов и авторов.
            anime_api_client: Клиент API аниме для заголовков карточек.
        """
        self._unit_of_work = unit_of_work
        self._anime_api_client = anime_api_client

    async def execute(self, query: HighlightDashboardQuery) -> HighlightDashboard:
        """Собрать дашборд хайлайтов с учётом фильтров.

        Args:
            query: Фильтры, сортировка и зритель дашборда.

        Returns:
            HighlightDashboard: Готовый дашборд с карточками и статистикой.
        """
        async with self._unit_of_work as uow:
            repository = uow.repository(HighlightRepository)
            highlights = await self._load(repository, query)
            engagement_map = await repository.get_engagement_map(
                [item.id for item in highlights if item.id is not None],
                viewer_user_id=query.viewer_user_id,
            )
            owner_map = await self._load_owners(uow, highlights)
        return await self._build_dashboard(highlights, query, engagement_map, owner_map)

    async def _load(
        self,
        repository: HighlightRepository,
        query: HighlightDashboardQuery,
    ) -> list[Highlight]:
        """Загрузить хайлайты личного дашборда.

        Args:
            repository: Репозиторий хайлайтов текущей транзакции.
            query: Параметры дашборда с идентификатором владельца.

        Returns:
            list[Highlight]: Хайлайты владельца либо пустой список без владельца.
        """
        if query.user_id is None:
            return []
        return await repository.get_by_user(query.user_id)

    async def _load_owners(
        self,
        unit_of_work: UnitOfWorkInterface,
        highlights: Sequence[Highlight],
    ) -> dict[int, User]:
        """Загрузить авторов хайлайтов одним запросом.

        Args:
            unit_of_work: Граница транзакции с доступом к репозиторию пользователей.
            highlights: Хайлайты, для которых нужны авторы.

        Returns:
            dict[int, User]: Авторы по идентификатору пользователя.
        """
        owner_ids = sorted({int(item.user_id) for item in highlights if item.user_id is not None})
        if not owner_ids:
            return {}
        users = await unit_of_work.repository(UserRepository).get_by_ids(owner_ids)
        return {user.id: user for user in users if user.id is not None}

    async def _build_dashboard(
        self,
        highlights: Sequence[Highlight],
        query: HighlightDashboardQuery,
        engagement_map: dict[int, HighlightEngagement],
        owner_map: dict[int, User],
    ) -> HighlightDashboard:
        """Разложить хайлайты по карточкам дашборда.

        Args:
            highlights: Исходные хайлайты без фильтрации.
            query: Фильтры и параметры отображения дашборда.
            engagement_map: Социальные метрики по идентификаторам хайлайтов.
            owner_map: Авторы хайлайтов по идентификатору пользователя.

        Returns:
            HighlightDashboard: Дашборд с карточками, группами и статистикой.
        """
        anime_cache: dict[int, AnimeMeta] = {}

        async def anime_meta(anime_id: int) -> AnimeMeta:
            """Получить карточку аниме из локального кэша запроса."""
            if anime_id not in anime_cache:
                anime_cache[anime_id] = await self._fetch_anime_meta(anime_id)
            return anime_cache[anime_id]

        filtered: list[Highlight] = []
        for highlight in highlights:
            if not self._matches(highlight, query, (await anime_meta(highlight.anime_id))[0]):
                continue
            filtered.append(highlight)
        filtered = self._sort_highlights(filtered, query.sort_by)

        cards: list[HighlightCard] = []
        counter: Counter[tuple[int, str]] = Counter()
        emotions: set[str] = set()
        categories: set[str] = set()
        total_duration = 0.0

        for highlight in filtered:
            anime_title, cover, watch_id, anime_original_title = await anime_meta(
                highlight.anime_id
            )
            duration = max(highlight.end_timestamp - highlight.start_timestamp, 0.0)
            counter[(highlight.anime_id, anime_title)] += 1
            if highlight.emotion:
                emotions.add(highlight.emotion)
            if highlight.category:
                categories.add(highlight.category)
            total_duration += duration
            engagement = engagement_map.get(highlight.id or 0)
            owner = owner_map.get(highlight.user_id) if highlight.user_id is not None else None
            cards.append(
                HighlightCard(
                    id=highlight.id or 0,
                    anime_id=highlight.anime_id,
                    anime_title=anime_title,
                    anime_cover=cover,
                    title=highlight.title or f"Момент {highlight.episode} серии",
                    category=highlight.category,
                    episode=highlight.episode,
                    start_timestamp=self._format_timestamp(highlight.start_timestamp),
                    end_timestamp=self._format_timestamp(highlight.end_timestamp),
                    duration_seconds=duration,
                    description=highlight.description or "",
                    is_spoiler=highlight.is_spoiler,
                    emotion=highlight.emotion,
                    created_at=highlight.created_at.strftime("%Y-%m-%d"),
                    likes_count=highlight.likes_count,
                    views_count=highlight.views_count,
                    comments_count=engagement.comments_count if engagement else 0,
                    is_liked=engagement.is_liked if engagement else False,
                    is_saved=engagement.is_saved if engagement else False,
                    watch_url=self._build_watch_url(
                        watch_id=watch_id,
                        episode=highlight.episode,
                        start_timestamp=highlight.start_timestamp,
                    ),
                    share_url=f"/highlights/share/{highlight.id}",
                    owner_user_id=highlight.user_id,
                    owner_username=owner.username if owner else None,
                    owner_avatar_url=owner.avatar_url if owner else None,
                    owner_profile_url=f"/users/{highlight.user_id}",
                    anime_original_title=anime_original_title,
                )
            )

        groups = [
            HighlightAnimeGroup(anime_id=item[0][0], anime_title=item[0][1], count=item[1])
            for item in counter.most_common()
        ]
        average_duration = (total_duration / len(cards)) if cards else 0.0

        return HighlightDashboard(
            items=cards,
            anime_groups=groups,
            emotions=sorted(emotions),
            categories=sorted(categories),
            stats=HighlightStats(
                total_highlights=len(cards),
                top_anime_title=groups[0].anime_title if groups else "Нет данных",
                average_duration_seconds=round(average_duration, 1),
            ),
            selected_anime_id=query.anime_id,
            selected_emotion=query.emotion,
            selected_category=query.category,
            selected_sort=query.sort_by if query.sort_by in {"recent", "popular"} else "recent",
            selected_date=query.created_date,
            selected_query=query.query,
            include_spoilers=query.include_spoilers,
        )

    async def _fetch_anime_meta(self, anime_id: int) -> AnimeMeta:
        """Получить заголовок, обложку и ссылку просмотра аниме.

        Args:
            anime_id: Идентификатор аниме.

        Returns:
            AnimeMeta: Заголовок, обложка, идентификатор для просмотра и оригинальное имя.
        """
        anime = await self._anime_api_client.get_by_id(anime_id)
        watch_id = anime_id
        if anime and anime.external_id:
            try:
                resolved_watch_id = int(str(anime.external_id).strip())
            except (TypeError, ValueError):
                resolved_watch_id = watch_id
            if resolved_watch_id > 0:
                watch_id = resolved_watch_id
        return (
            anime.title if anime and anime.title else f"Anime #{anime_id}",
            anime.cover_url if anime else None,
            watch_id,
            anime.original_title if anime and anime.original_title else None,
        )

    def _matches(
        self,
        highlight: Highlight,
        query: HighlightDashboardQuery,
        anime_title: str,
    ) -> bool:
        """Проверить, проходит ли хайлайт фильтры дашборда.

        Args:
            highlight: Проверяемый хайлайт.
            query: Фильтры дашборда.
            anime_title: Заголовок аниме для текстового поиска.

        Returns:
            bool: True, если хайлайт попадает в выборку.
        """
        if query.anime_id is not None and highlight.anime_id != query.anime_id:
            return False
        if query.emotion and (highlight.emotion or "") != query.emotion:
            return False
        if query.category and (highlight.category or "") != query.category:
            return False
        if query.created_date and highlight.created_at.strftime("%Y-%m-%d") != query.created_date:
            return False
        if not query.include_spoilers and highlight.is_spoiler:
            return False
        haystack = (
            f"{anime_title} {highlight.title or ''} {highlight.description or ''} "
            f"{highlight.category or ''} {highlight.emotion or ''}"
        ).lower()
        return not query.query or query.query.lower() in haystack

    def _sort_highlights(self, highlights: Sequence[Highlight], sort_by: str) -> list[Highlight]:
        """Отсортировать хайлайты по выбранному полю.

        Args:
            highlights: Отфильтрованные хайлайты.
            sort_by: Критерий сортировки: 'popular' или 'recent'.

        Returns:
            list[Highlight]: Отсортированный список.
        """
        if sort_by == "popular":
            return sorted(highlights, key=self._popularity_score, reverse=True)
        return sorted(highlights, key=lambda item: item.created_at, reverse=True)

    def _popularity_score(self, highlight: Highlight) -> float:
        """Посчитать оценку популярности с бонусом за свежесть.

        Args:
            highlight: Хайлайт для оценки.

        Returns:
            float: Взвешенная сумма лайков, просмотров и свежести.
        """
        age_hours = max(
            (utc_now() - highlight.created_at).total_seconds() / 3600,
            0.0,
        )
        freshness_bonus = max(72.0 - age_hours, 0.0) / 12.0
        return (
            float(highlight.likes_count or 0) * 4.0
            + float(highlight.views_count or 0) * 2.0
            + freshness_bonus
        )

    def _format_timestamp(self, seconds: float) -> str:
        """Отформатировать секунды как минуты и секунды.

        Args:
            seconds: Смещение внутри серии в секундах.

        Returns:
            str: Смещение в формате ``MM:SS``.
        """
        minutes = int(seconds // 60)
        return f"{minutes:02d}:{int(seconds % 60):02d}"

    def _build_watch_url(self, watch_id: int, episode: int, start_timestamp: float) -> str:
        """Собрать ссылку на страницу просмотра с начала фрагмента.

        Args:
            watch_id: Идентификатор аниме для страницы просмотра.
            episode: Номер серии.
            start_timestamp: Начало фрагмента в секундах.

        Returns:
            str: Ссылка на просмотр с параметрами серии и смещения.
        """
        start_at = max(int(float(start_timestamp or 0.0)), 0)
        return f"/watch/{watch_id}?episode={episode}&start_at={start_at}"
