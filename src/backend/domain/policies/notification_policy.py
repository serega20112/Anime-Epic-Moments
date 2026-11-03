"""Правила формулировок уведомлений мобильного клиента.

Текст уведомления собирается здесь, а не в местах его создания, чтобы тон
реплик для лайка, комментария и подписки жил в одном месте и был единообразным.
"""

from __future__ import annotations

HIGHLIGHT_LIKE_TEXT = "Ваш хайлайт оценили"
HIGHLIGHT_COMMENT_TEXT = "Ваш хайлайт прокомментировали"
NEW_FOLLOWER_TEXT = "На вас подписался новый пользователь"


def notification_text(kind: str) -> str:
    """Вернуть текст уведомления по его типу.

    Args:
        kind: Тип события из набора видов уведомлений.

    Returns:
        str: Формулировка для показа человеку либо пустая строка для неизвестного
            типа.
    """
    from backend.domain.entities.notification.notification import (
        KIND_HIGHLIGHT_COMMENT,
        KIND_HIGHLIGHT_LIKE,
        KIND_NEW_FOLLOWER,
    )

    mapping = {
        KIND_HIGHLIGHT_LIKE: HIGHLIGHT_LIKE_TEXT,
        KIND_HIGHLIGHT_COMMENT: HIGHLIGHT_COMMENT_TEXT,
        KIND_NEW_FOLLOWER: NEW_FOLLOWER_TEXT,
    }
    return mapping.get(kind, "")
