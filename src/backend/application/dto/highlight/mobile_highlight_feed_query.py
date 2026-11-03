"""Параметры ленты хайлайтов для мобильного клиента."""

from __future__ import annotations

from dataclasses import dataclass

MODE_FOR_YOU = "for_you"
MODE_FOLLOWING = "following"
MODE_TOP = "top"
FEED_MODES = frozenset({MODE_FOR_YOU, MODE_FOLLOWING, MODE_TOP})


@dataclass(frozen=True, slots=True)
class MobileHighlightFeedQuery:
    """Режим, страница и зритель мобильной ленты хайлайтов.

    Attributes:
        mode: Режим ленты: ``for_you``, ``following`` или ``top``.
        page: Номер страницы, начиная с единицы.
        per_page: Размер страницы.
        include_spoilers: Показывать ли хайлайты со спойлерами.
        viewer_user_id: Идентификатор зрителя для отметок и персонализации.
    """

    mode: str = MODE_FOR_YOU
    page: int = 1
    per_page: int = 12
    include_spoilers: bool = False
    viewer_user_id: int | None = None
