from __future__ import annotations

import pytest

from backend.domain import Highlight, InvalidHighlightTimeError


@pytest.mark.parametrize(("start", "end"), [(10.0, 10.0), (12.0, 5.0)])
def test_highlight_requires_end_timestamp_greater_than_start(start, end):
    """Проверяем, что Highlight отклоняет некорректный интервал времени."""
    with pytest.raises(InvalidHighlightTimeError):
        Highlight(
            user_id=1,
            anime_id=7,
            episode=1,
            start_timestamp=start,
            end_timestamp=end,
        )


def test_highlight_edit_updates_fields_and_revalidates_interval():
    """Проверяем, что edit обновляет поля хайлайта, включая title и category, и повторно валидирует интервал."""
    highlight = Highlight(
        user_id=1,
        anime_id=7,
        episode=1,
        start_timestamp=5.0,
        end_timestamp=15.0,
        title="before",
        category="драма",
        description="before",
        is_spoiler=False,
    )

    highlight.edit(
        start_timestamp=8.0,
        end_timestamp=20.0,
        title="after",
        category="бой",
        description="after",
        is_spoiler=True,
        emotion="hype",
    )

    assert highlight.start_timestamp == 8.0
    assert highlight.end_timestamp == 20.0
    assert highlight.title == "after"
    assert highlight.category == "бой"
    assert highlight.description == "after"
    assert highlight.is_spoiler is True
    assert highlight.emotion == "hype"


@pytest.mark.parametrize(
    ("operations", "expected_likes", "expected_views"),
    [(["add", "add", "remove"], 1, 0), (["remove", "remove", "view"], 0, 1)],
)
def test_highlight_counters_work_for_likes_and_views(operations, expected_likes, expected_views):
    """Проверяем, что счетчики лайков и просмотров корректно обновляются и не уходят ниже нуля."""
    highlight = Highlight(
        user_id=1,
        anime_id=7,
        episode=1,
        start_timestamp=5.0,
        end_timestamp=10.0,
    )

    for operation in operations:
        if operation == "view":
            highlight.add_view()
        else:
            getattr(highlight, f"{operation}_like")()

    assert highlight.likes_count == expected_likes
    assert highlight.views_count == expected_views
