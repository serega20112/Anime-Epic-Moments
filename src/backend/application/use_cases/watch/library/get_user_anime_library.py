"""Чтение библиотеки просмотра пользователя."""

from __future__ import annotations

from backend.application.dto.watch import GetUserLibraryQuery
from backend.application.interface.repositories.watch_repository import WatchRepository
from backend.application.interface.services import AnimeApiClientInterface
from backend.application.interface.unit_of_work import UnitOfWorkInterface
from backend.domain.entities.anime.anime import Anime
from backend.domain.value_objects.watch.library_cards import LibraryAnimeCard


class GetUserAnimeLibraryUseCase:
    """Возвращает карточки дневника пользователя по статусу просмотра."""

    def __init__(
        self,
        uow: UnitOfWorkInterface,
        anime_api_client: AnimeApiClientInterface,
    ) -> None:
        """Инициализирует сценарий чтения библиотеки.

        Args:
            uow: Единица работы, через которую берётся репозиторий.
            anime_api_client: Клиент каталога для дополнения карточек.
        """
        self._uow = uow
        self._anime_api_client = anime_api_client

    async def execute(self, query: GetUserLibraryQuery) -> list[LibraryAnimeCard]:
        """Собирает карточки дневника, дополняя их данными каталога.

        Записи читаются одной короткой транзакцией, а обращения к каталогу идут
        после её закрытия: соединение с базой не удерживается время сетевых
        вызовов. Пустой статус в запросе означает весь дневник.

        Args:
            query: Владелец дневника и необязательный фильтр по статусу.

        Returns:
            list[LibraryAnimeCard]: Карточки в порядке последнего просмотра.
        """
        async with self._uow as uow:
            statuses = await uow.repository(WatchRepository).get_statuses_by_user(query.user_id)
        wanted = query.status.strip()
        entries = [item for item in statuses if not wanted or item.status == wanted]
        entries.sort(key=lambda item: item.last_watched_at or item.updated_at, reverse=True)

        result: list[LibraryAnimeCard] = []
        for entry in entries:
            anime = await self._resolve_anime(entry.anime_id)
            result.append(
                LibraryAnimeCard(
                    anime=anime,
                    status=entry.status,
                    current_episode=entry.current_episode,
                    rating=entry.rating,
                    last_watched_at=self._format_date(entry.last_watched_at or entry.updated_at),
                )
            )
        return result

    async def _resolve_anime(self, anime_id: int) -> Anime:
        """Получить карточку тайтла из каталога либо собрать запасную заглушку.

        Args:
            anime_id: Идентификатор аниме из дневника.

        Returns:
            Anime: Карточка каталога либо заглушка с идентификатором в названии.
        """
        anime = await self._anime_api_client.get_by_id(anime_id)
        if anime is not None:
            return anime
        return Anime(external_id=anime_id, title=f"Anime #{anime_id}")

    @staticmethod
    def _format_date(value) -> str | None:
        """Отформатировать дату в текстовый вид либо вернуть None.

        Args:
            value: Объект даты либо None.

        Returns:
            str | None: Дата ``YYYY-MM-DD`` либо None при отсутствии значения.
        """
        return value.strftime("%Y-%m-%d") if value else None
