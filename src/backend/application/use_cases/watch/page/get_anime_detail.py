"""Сценарий карточки тайтла для мобильного клиента.

Карточка, источники, статус, оценка и позиция текущей серии берутся из
сценария страницы просмотра; здесь добавляются лишь производные данные:
признак «в избранном» и по-серийный прогресс по дневнику зрителя. Так правило
доступных серий и приоритета источников не дублируется.
"""

from __future__ import annotations

from backend.application.dto import GetFavoriteIdsQuery, WatchPageQuery
from backend.application.interface.repositories.watch_repository import WatchRepository
from backend.application.interface.unit_of_work import UnitOfWorkInterface
from backend.application.use_cases.favorite.get_favorite_ids import GetFavoriteIdsUseCase
from backend.application.use_cases.watch.page.get_watch_page import GetWatchPageUseCase
from backend.domain.value_objects.watch.detail import AnimeDetail, EpisodeProgress

STATUS_COMPLETED = "completed"


class GetAnimeDetailUseCase:
    """Собирает карточку тайтла с избранным и по-серийным прогрессом."""

    def __init__(
        self,
        uow: UnitOfWorkInterface,
        watch_page_use_case: GetWatchPageUseCase,
        favorite_ids_use_case: GetFavoriteIdsUseCase,
    ) -> None:
        """Инициализирует сценарий карточки тайтла.

        Args:
            uow: Единица работы для чтения статуса дневника.
            watch_page_use_case: Сценарий страницы просмотра как источник ядра.
            favorite_ids_use_case: Сценарий идентификаторов избранного зрителя.
        """
        self._uow = uow
        self._watch_page_use_case = watch_page_use_case
        self._favorite_ids_use_case = favorite_ids_use_case

    async def execute(self, query: WatchPageQuery) -> AnimeDetail:
        """Собрать карточку тайтла с производными состояниями зрителя.

        Args:
            query: Идентификаторы тайтла и зрителя, серия и предпочтения плеера.

        Returns:
            AnimeDetail: Карточка с избранностью и прогрессом по сериям.
        """
        page = await self._watch_page_use_case.execute(query)
        favorites = False
        current_episode = 0
        completed = False
        if query.user_id is not None:
            favorite_ids = await self._favorite_ids_use_case.execute(
                GetFavoriteIdsQuery(user_id=query.user_id)
            )
            favorites = page.anime_id in favorite_ids
            async with self._uow as uow:
                status = await uow.repository(WatchRepository).get_status(
                    user_id=query.user_id, anime_id=page.anime_id
                )
            if status is not None:
                current_episode = status.current_episode or 0
                completed = status.status == STATUS_COMPLETED
        episodes = [
            EpisodeProgress(
                number=number,
                watched=completed or number < current_episode,
                position_seconds=page.last_position_seconds if number == page.episode else 0.0,
            )
            for number in page.episode_options
        ]
        return AnimeDetail(page=page, favorites=favorites, episodes=episodes)
