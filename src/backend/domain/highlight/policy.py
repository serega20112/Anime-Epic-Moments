"""HighlightPolicy — бизнес-правила для Highlight, например лимиты добавлений для гостей, проверка контента и спойлеров"""

from backend.domain.highlight.entity import Highlight


class HighlightPolicy:
    """Правила для Highlight.

    Включают лимит для гостей и проверку на запрещённый контент.
    """

    GUEST_MAX_PER_HOUR = 5

    @staticmethod
    async def can_add_highlight(user_id: int, highlights_this_hour: int) -> bool:
        """Проверяет, можно ли добавить хайлайт.

        Если user_id=None → гость.
        """
        if user_id is None:
            return highlights_this_hour < HighlightPolicy.GUEST_MAX_PER_HOUR
        return True  #

    @staticmethod
    async def filter_spoiler_content(description: str) -> bool:
        """Проверяет описание на запрещённый контент.

        Возвращает True, если описание безопасно.
        """
        banned_words = ["мат", "спам", "вред"]  # пример
        description_lower = description.lower()
        return not any(word in description_lower for word in banned_words)

    @staticmethod
    async def should_hide_spoiler(highlight: Highlight) -> bool:
        """Возвращает True, если спойлер нужно скрывать в UI"""
        return highlight.is_spoiler
