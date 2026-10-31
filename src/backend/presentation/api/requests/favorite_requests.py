"""Модели запросов избранного."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class AddFavoriteRequest(BaseModel):
    """Тело запроса добавления аниме в избранное.

    Клиент может прислать ``user_id``: поле игнорируется, потому что владелец
    берётся только из сессии.

    Attributes:
        anime_id: Идентификатор аниме.
        title: Название аниме для снимка карточки.
        description: Описание аниме для снимка карточки.
        cover_url: Ссылка на обложку.
        genres: Жанры списком или строкой через запятую.
        original_title: Оригинальное название.
    """

    model_config = ConfigDict(extra="ignore")

    anime_id: int = Field(gt=0)
    title: str | None = None
    description: str | None = None
    cover_url: str | None = None
    genres: list[str] | str | None = None
    original_title: str | None = None


class RemoveFavoriteRequest(BaseModel):
    """Тело запроса удаления аниме из избранного.

    Attributes:
        anime_id: Идентификатор аниме.
    """

    model_config = ConfigDict(extra="ignore")

    anime_id: int = Field(gt=0)
