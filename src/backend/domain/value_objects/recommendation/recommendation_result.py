"""Значимый объект результата рекомендаций."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class RecommendationResult:
    """Результат подбора рекомендаций с пояснением.

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

    anime_id: int
    reason: str
    similarity_score: float
    title: str
    description: str
    image_url: str | None
    genres: list[str] = field(default_factory=list)
    watch_url: str | None = None
