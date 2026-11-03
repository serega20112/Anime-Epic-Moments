"""Чтение истории просмотров пользователя."""

from __future__ import annotations

from backend.application.dto.watch import GetUserHistoryQuery
from backend.application.interface.repositories.watch_repository import WatchRepository
from backend.application.interface.services import AnimeApiClientInterface
from backend.application.interface.unit_of_work import UnitOfWorkInterface
from backend.domain.entities.anime.anime import Anime
from backend.domain.value_objects.watch.library_cards import HistoryAnimeCard


class GetUserViewingHistoryUseCase:
    """Возвращает карточки недавних сессий просмотра пользователя."""

    def __init__(
        self,
        uow: UnitOfWorkInterface,
        anime_api_client: AnimeApiClientInterface,
    ) -> None:
        """Инициализирует сценарий чтения истории.

        Args:
            uow: Единица работы, через которую берётся репозиторий.
            anime_api_client: Клиент каталога для дополнения карточек.
        """
        self._uow = uow
        self._anime_api_client = anime_api_client

    async def execute(self, query: GetUserHistoryQuery) -> list[HistoryAnimeCard]:
        """Собирает карточки истории, дополняя их данными каталога.

        Сессии читаются одной короткой транзакцией без повторов одной серии, а
        обращения к каталогу идут после закрытия транзакции.

        Args:
            query: Владелец истории и максимальное число записей.

        Returns:
            list[HistoryAnimeCard]: Карточки в порядке последних сессий.
        """
        async with self._uow as uow:
            sessions = await uow.repository(WatchRepository).get_recent_viewing_sessions(
                query.user_id, limit=query.limit
            )

        result: list[HistoryAnimeCard] = []
        for session in sessions:
            anime = await self._resolve_anime(session.anime_id)
            result.append(
                HistoryAnimeCard(
                    anime=anime,
                    episode=session.episode,
                    position_seconds=session.position_seconds,
                    watched_at=session.updated_at.strftime("%Y-%m-%d"),
                )
            )
        return result

    async def _resolve_anime(self, anime_id: int) -> Anime:
        """Получить карточку тайтла из каталога либо собрать запасную заглушку.

        Args:
            anime_id: Идентификатор аниме из сессии.

        Returns:
            Anime: Карточка каталога либо заглушка с идентификатором в названии.
        """
        anime = await self._anime_api_client.get_by_id(anime_id)
        if anime is not None:
            return anime
        return Anime(external_id=anime_id, title=f"Anime #{anime_id}")
