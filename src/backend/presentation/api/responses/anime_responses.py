"""Модели ответов JSON-маршрутов каталога аниме."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from backend.presentation.api.responses.pagination import Page


class AnimeCardResponse(BaseModel):
    """Карточка тайтла в представлении внешнего каталога.

    Attributes:
        external_id: Идентификатор тайтла во внешнем каталоге.
        title: Название тайтла.
        original_title: Оригинальное название либо None.
        description: Описание тайтла либо None.
        genres: Жанры тайтла.
        year: Год выпуска либо None.
        rating: Рейтинг по шкале каталога либо None.
        cover_url: Ссылка на обложку либо None.
        episode_count: Число серий либо None.
    """

    model_config = ConfigDict(from_attributes=True)

    external_id: int | str
    title: str
    original_title: str | None = None
    description: str | None = None
    genres: list[str] = []
    year: int | None = None
    rating: float | None = None
    cover_url: str | None = None
    episode_count: int | None = None


class GenreFacetResponse(BaseModel):
    """Жанр с числом тайтлов, встретившихся в текущей выдаче.

    Attributes:
        name: Название жанра.
        count: Число тайтлов жанра на странице фильтра.
    """

    model_config = ConfigDict(from_attributes=True)

    name: str
    count: int


class AnimeCatalogPage(Page[AnimeCardResponse]):
    """Страница каталога вместе с фасетами жанров для панели фильтров.

    Attributes:
        total_is_exact: True, если ``total`` подсчитан точно, а не оценочно.
        genre_facets: Счётчики по жанрам для панели фильтров.
    """

    total_is_exact: bool = True
    genre_facets: list[GenreFacetResponse] = []


class AnimeSearchResultResponse(BaseModel):
    """Выдача семантического поиска с признаком возрастной границы.

    Attributes:
        items: Найденные тайтлы.
        requires_age_confirmation: True, если требуется подтверждение возраста.
        message: Пояснение для клиента либо None.
    """

    model_config = ConfigDict(from_attributes=True)

    items: list[AnimeCardResponse] = []
    requires_age_confirmation: bool = False
    message: str | None = None
