"""Порт клиента языковой модели."""

from __future__ import annotations

from abc import ABC, abstractmethod


class LLMClientInterface(ABC):
    """Запросы к языковой модели для поиска и описания вкусов.

    Порт описывает только те обращения, которые действительно нужны сценариям:
    поиск тайтлов по описанию выполняет каталог, а не модель, и объявление
    такого метода здесь лишь создавало бы неисполнимый контракт.
    """

    @abstractmethod
    async def build_search_queries_with_meta(
        self,
        description: str,
        genre_hint: str | None = None,
        year_from: int | None = None,
        year_to: int | None = None,
        min_rating: int | None = None,
        age_rating: str = "all",
        allow_adult: bool = False,
    ) -> tuple[list[str], str, str | None]:
        """Собрать поисковые запросы вместе с метаданными провайдера.

        Args:
            description: Описание тайтла на естественном языке.
            genre_hint: Подсказка по жанру.
            year_from: Нижняя граница года выпуска.
            year_to: Верхняя граница года выпуска.
            min_rating: Минимальный рейтинг.
            age_rating: Возрастная граница выдачи.
            allow_adult: Разрешить adult-контент.

        Returns:
            tuple[list[str], str, str | None]: Запросы, режим работы провайдера
            и текст ошибки, если ответ не удалось получить.
        """

    @abstractmethod
    async def describe_taste_profile(self, profile_data: dict, fallback: str) -> str:
        """Составить описание вкусового профиля.

        Args:
            profile_data: Сведённые данные просмотров пользователя.
            fallback: Текст, возвращаемый при недоступности модели.

        Returns:
            str: Описание вкусов либо ``fallback``.
        """
