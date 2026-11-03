"""Модели ответов избранного."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class FavoriteIdsResponse(BaseModel):
    """Ответ со списком идентификаторов избранного.

    Attributes:
        user_id: Идентификатор владельца избранного.
        anime_ids: Идентификаторы избранных аниме.
    """

    user_id: int
    anime_ids: list[int]


class FavoriteAnimeCardResponse(BaseModel):
    """Карточка избранного тайтла в JSON-представлении.

    Отражает доменную карточку :class:`FavoriteAnimeCard` и принимает её
    напрямую (``from_attributes``), поэтому маршрут не собирает словарь вручную.

    Attributes:
        anime_id: Идентификатор аниме.
        title: Название тайтла.
        description: Описание тайтла.
        cover_url: Ссылка на обложку либо None.
        genres: Жанры тайтла.
        watch_url: Ссылка на страницу просмотра.
        added_at: Дата добавления в текстовом виде.
        original_title: Оригинальное название либо None.
    """

    model_config = ConfigDict(from_attributes=True)

    anime_id: int
    title: str
    description: str
    cover_url: str | None = None
    genres: list[str] = []
    watch_url: str
    added_at: str
    original_title: str | None = None
