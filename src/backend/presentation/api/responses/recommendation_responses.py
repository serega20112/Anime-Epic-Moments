"""Модели ответов JSON-маршрутов рекомендаций."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class RecommendationItemResponse(BaseModel):
    """Одна рекомендация в JSON-представлении.

    Attributes:
        anime_id: Идентификатор тайтла во внешнем каталоге.
        reason: Пояснение, почему тайтл предложен.
        similarity_score: Балл близости к запросу или вкусам пользователя.
        title: Название тайтла.
        description: Описание тайтла.
        image_url: Ссылка на обложку либо None.
        genres: Жанры тайтла.
        watch_url: Ссылка на страницу просмотра либо None.
    """

    model_config = ConfigDict(from_attributes=True)

    anime_id: int
    reason: str
    similarity_score: float
    title: str
    description: str
    image_url: str | None = None
    genres: list[str] = Field(default_factory=list)
    watch_url: str | None = None
