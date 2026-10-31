"""Ограничения частоты и допустимые размеры пользовательских данных."""

from __future__ import annotations

import os


def support_ticket_rate_limit() -> int:
    """Вернуть лимит создания обращений в поддержку."""
    return int(os.getenv("SUPPORT_TICKET_RATE_LIMIT", "3"))


def highlight_comment_rate_limit() -> int:
    """Вернуть лимит создания комментариев к хайлайтам."""
    return int(os.getenv("HIGHLIGHT_COMMENT_RATE_LIMIT", "30"))


def highlight_rate_window_seconds() -> int:
    """Вернуть окно ограничения частоты для хайлайтов в секундах."""
    return int(os.getenv("HIGHLIGHT_RATE_WINDOW_SECONDS", "60"))


def anime_query_limit_max() -> int:
    """Вернуть предельный размер выдачи поиска аниме."""
    return int(os.getenv("ANIME_QUERY_LIMIT_MAX", "50"))


def anime_title_max_length() -> int:
    """Вернуть предельную длину названия аниме."""
    return int(os.getenv("ANIME_TITLE_MAX_LENGTH", "200"))


def anime_description_max_length() -> int:
    """Вернуть предельную длину описания аниме."""
    return int(os.getenv("ANIME_DESCRIPTION_MAX_LENGTH", "500"))


def anime_genre_hint_max_length() -> int:
    """Вернуть предельную длину подсказки жанра."""
    return int(os.getenv("ANIME_GENRE_HINT_MAX_LENGTH", "80"))


def anime_autocomplete_limit_max() -> int:
    """Вернуть предельный размер выдачи автодополнения."""
    return int(os.getenv("ANIME_AUTOCOMPLETE_LIMIT_MAX", "20"))
