"""Порт клиента внешнего API каталога аниме."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence

from backend.domain.entities.anime.anime import Anime
from backend.domain.value_objects.anime.catalog_page import CatalogPage


class AnimeApiClientInterface(ABC):
    """Источник данных каталога аниме.

    Порт описывает ровно те методы, которыми пользуются сценарии: объявление
    метода, которого нет в реализациях, ломает подмену клиента, а отсутствие
    объявленного — позволяет сценарию вызвать метод, мимо которого «умная»
    заглушка не проходит.
    """

    @abstractmethod
    async def get_by_id(self, anime_id: int) -> Anime | None:
        """Получить карточку аниме по идентификатору.

        Args:
            anime_id: Идентификатор тайтла во внешнем каталоге.

        Returns:
            Anime | None: Карточка тайтла либо None, если каталог его не знает.
        """

    @abstractmethod
    async def search_by_title(
        self,
        title: str,
        limit: int = 10,
        include_adult: bool = False,
    ) -> list[Anime]:
        """Найти аниме по названию.

        Args:
            title: Поисковый запрос.
            limit: Максимальное число результатов.
            include_adult: Разрешить adult-контент в выдаче.

        Returns:
            list[Anime]: Найденные карточки без пропущенных дублей.
        """

    @abstractmethod
    async def search_by_description(
        self,
        description: str,
        year_from: int | None = None,
        year_to: int | None = None,
        min_rating: int | None = None,
        include_adult: bool = False,
        limit: int = 10,
    ) -> list[Anime]:
        """Найти аниме по описанию на естественном языке.

        Args:
            description: Текстовое описание того, что ищет пользователь.
            year_from: Нижняя граница года выпуска.
            year_to: Верхняя граница года выпуска.
            min_rating: Минимальный рейтинг.
            include_adult: Разрешить adult-контент в выдаче.
            limit: Максимальное число результатов.

        Returns:
            list[Anime]: Карточки тайтлов, подходящих под описание.
        """

    @abstractmethod
    async def get_top_anime(self, limit: int = 25) -> list[Anime]:
        """Получить популярные тайтлы как пул кандидатов для рекомендаций.

        Args:
            limit: Максимальное число карточек.

        Returns:
            list[Anime]: Карточки популярных тайтлов.
        """

    @abstractmethod
    async def get_season_popular(self, year: int, season: str, limit: int = 10) -> list[Anime]:
        """Получить популярное аниме указанного сезона.

        Args:
            year: Год сезона.
            season: Название сезона (winter, spring, summer, fall).
            limit: Максимальное число результатов.

        Returns:
            list[Anime]: Карточки тайтлов сезона.
        """

    @abstractmethod
    async def filter_catalog(
        self,
        *,
        genres: Sequence[str] = (),
        media_type: str = "",
        status: str = "",
        year_from: int | None = None,
        year_to: int | None = None,
        min_score: float | None = None,
        sort: str = "rating",
        order: str = "desc",
        page: int = 1,
        per_page: int = 25,
    ) -> CatalogPage:
        """Просмотреть каталог с фильтрами в стиле Anixart.

        Провайдер объединяет выбранные жанры по правилу «или»: ни один из
        внешних API не умеет одновременно ограничивать набор жанров.

        Args:
            genres: Жанры для объединения по правилу «или».
            media_type: Тип тайтла (tv, movie, ova и тому подобное).
            status: Статус выхода тайтла.
            year_from: Нижняя граница года выпуска.
            year_to: Верхняя граница года выпуска.
            min_score: Минимальный рейтинг.
            sort: Поле сортировки.
            order: Направление сортировки.
            page: Номер страницы выдачи.
            per_page: Размер страницы.

        Returns:
            CatalogPage: Страница каталога с карточками и общим числом.
        """
