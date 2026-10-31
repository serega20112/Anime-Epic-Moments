"""Результат поиска аниме с пояснением совпадения."""

from __future__ import annotations

from dataclasses import dataclass, field

from backend.domain.entities.anime.anime import Anime


@dataclass(frozen=True, slots=True)
class SearchAnimeByDescriptionResult:
    """Результат поиска аниме по описанию с метаданными age-gate.

    Attributes:
        items: Найденные карточки тайтлов.
        requires_age_confirmation: Нужен ли клик по «мне есть 18».
        message: Текст-предупреждение для клиента либо None.
    """

    items: list[Anime] = field(default_factory=list)
    requires_age_confirmation: bool = False
    message: str | None = None
