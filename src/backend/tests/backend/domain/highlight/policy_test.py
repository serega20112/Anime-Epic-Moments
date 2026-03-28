from __future__ import annotations

import pytest

from src.backend.domain.highlight.entity import Highlight
from src.backend.domain.highlight.policy import HighlightPolicy


@pytest.mark.parametrize(
    ("user_id", "highlights_this_hour", "expected"),
    [
        (None, 4, True),
        (None, 5, False),
        (10, 100, True),
    ],
)
def test_can_add_highlight_applies_guest_limit(user_id, highlights_this_hour, expected):
    """Проверяем, что policy ограничивает гостей по количеству хайлайтов в час."""
    result = HighlightPolicy.can_add_highlight(user_id, highlights_this_hour)

    assert result is expected


@pytest.mark.parametrize(
    ("description", "expected"),
    [
        ("красивый момент без спама", False),
        ("очень вредный спам-контент", False),
        ("эмоциональный safe highlight", True),
    ],
)
def test_filter_spoiler_content_filters_banned_words(description, expected):
    """Проверяем, что policy отбрасывает описание с запрещенными маркерами."""
    result = HighlightPolicy.filter_spoiler_content(description)

    assert result is expected


@pytest.mark.parametrize("is_spoiler", [False, True])
def test_should_hide_spoiler_returns_highlight_flag(is_spoiler):
    """Проверяем, что policy возвращает текущее spoiler-состояние хайлайта."""
    highlight = Highlight(
        user_id=1,
        anime_id=8,
        episode=2,
        start_timestamp=1.0,
        end_timestamp=2.0,
        is_spoiler=is_spoiler,
    )

    assert HighlightPolicy.should_hide_spoiler(highlight) is is_spoiler
