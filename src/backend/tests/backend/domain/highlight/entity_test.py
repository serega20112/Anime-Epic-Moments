from __future__ import annotations

import pytest

from src.backend.domain.highlight.entity import Highlight, InvalidHighlightTimeError


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
    """Проверяем, что edit обновляет поля хайлайта и повторно валидирует интервал."""
    highlight = Highlight(
        user_id=1,
        anime_id=7,
        episode=1,
        start_timestamp=5.0,
        end_timestamp=15.0,
        description="before",
        is_spoiler=False,
    )

    highlight.edit(
        start_timestamp=8.0,
        end_timestamp=20.0,
        description="after",
        is_spoiler=True,
    )

    assert highlight.start_timestamp == 8.0
    assert highlight.end_timestamp == 20.0
    assert highlight.description == "after"
    assert highlight.is_spoiler is True


@pytest.mark.parametrize(
    ("operations", "expected"),
    [
        (["add", "add", "remove"], 1),
        (["remove", "remove"], 0),
    ],
)
def test_highlight_like_counter_never_goes_below_zero(operations, expected):
    """Проверяем, что счетчик лайков корректно растет и не уходит ниже нуля."""
    highlight = Highlight(
        user_id=1,
        anime_id=7,
        episode=1,
        start_timestamp=5.0,
        end_timestamp=10.0,
    )

    for operation in operations:
        getattr(highlight, f"{operation}_like")()

    assert highlight.likes_count == expected
