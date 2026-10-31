"""Бизнес-правила агрегата хайлайта."""

import re

from backend.domain.aggregates.highlight.highlight import Highlight


class HighlightPolicy:
    """Правила для хайлайта.

    Включают лимит добавления для гостей и проверку запрещённого контента.
    """

    GUEST_MAX_PER_HOUR = 5

    BANNED_PATTERNS = (
        re.compile(r"\bмат\b"),
        re.compile(r"\bспам\b"),
        re.compile(r"\bвред\w*\b"),
    )

    @staticmethod
    def can_add_highlight(user_id: int | None, highlights_this_hour: int) -> bool:
        """Проверяет, можно ли добавить хайлайт.

        Args:
            user_id: Идентификатор пользователя либо None для гостя.
            highlights_this_hour: Сколько хайлайтов гость добавил за час.

        Returns:
            bool: True, если добавление укладывается в лимит.
        """
        if user_id is None:
            return highlights_this_hour < HighlightPolicy.GUEST_MAX_PER_HOUR
        return True

    @staticmethod
    def is_content_allowed(text: str) -> bool:
        """Проверяет текст хайлайта на запрещённый контент.

        Совпадение ищется по границам слов, поэтому «математика» или «комната»
        не считаются нарушением, в отличие от подстрочного поиска.

        Args:
            text: Проверяемый текст.

        Returns:
            bool: True, если текст не содержит запрещённых слов.
        """
        normalized = str(text or "").lower()
        return not any(pattern.search(normalized) for pattern in HighlightPolicy.BANNED_PATTERNS)

    @staticmethod
    def should_hide_spoiler(highlight: Highlight) -> bool:
        """Определяет, нужно ли скрывать спойлер в интерфейсе.

        Args:
            highlight: Проверяемый хайлайт.

        Returns:
            bool: True, если хайлайт отмечен как спойлер.
        """
        return highlight.is_spoiler
