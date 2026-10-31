"""Модели запросов оценок."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from backend.domain.entities.rating.anime_rating import UserAnimeRating


class RateAnimeRequest(BaseModel):
    """Оценка аниме, присланная формой страницы просмотра.

    Attributes:
        anime_id: Идентификатор аниме.
        score: Оценка по десятибалльной шкале.
    """

    model_config = ConfigDict(extra="ignore")

    anime_id: int = Field(gt=0)
    score: int = Field(ge=UserAnimeRating.SCORE_MIN, le=UserAnimeRating.SCORE_MAX)
