"""Параметры запроса главной страницы аниме."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class HomePageQuery:
    """Параметры сборки главной страницы.

    Attributes:
        moment: Момент, на который определяется сезон; None — текущее время.
    """

    moment: datetime | None = None
