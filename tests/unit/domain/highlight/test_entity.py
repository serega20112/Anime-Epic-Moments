from __future__ import annotations

import pytest

from backend.domain.highlight.entity import Highlight, InvalidHighlightTimeError


class TestHighlightValidation:
    """Юнит-тесты валидации интервала хронометража Highlight."""

    @pytest.mark.unit
    @pytest.mark.parametrize("start", [10.0, 12.0])
    async def test_requires_end_timestamp_greater_than_start(self, start):
        """Что тестируем: валидацию временного интервала при создании Highlight.

        Что передаём: интервал, где end_timestamp не больше start_timestamp.
        Что ожидаем: выбрасывается InvalidHighlightTimeError.
        """
        with pytest.raises(InvalidHighlightTimeError):
            Highlight(
                user_id=1,
                anime_id=7,
                episode=1,
                start_timestamp=start,
                end_timestamp=10.0,
            )


class TestHighlightEdit:
    """Юнит-тесты метода edit сущности Highlight."""

    @pytest.mark.unit
    async def test_edit_updates_fields_and_revalidates_interval(self):
        """Что тестируем: метод edit.

        Что передаём: новые значения таймкодов, заголовка, категории, описания, is_spoiler и emotion.
        Что ожидаем: все поля обновляются, а интервал остаётся валидным.
        """
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

        await highlight.edit(
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


class TestHighlightCounters:
    """Юнит-тесты счётчиков лайков и просмотров Highlight."""

    @pytest.mark.unit
    @pytest.mark.parametrize(
        ("operations", "expected_likes", "expected_views"),
        [
            (["like", "like"], 2, 0),
            (["view", "view"], 0, 2),
            (["like", "view", "like"], 2, 1),
        ],
    )
    async def test_counters_update_for_likes_and_views(
        self,
        operations,
        expected_likes,
        expected_views,
    ):
        """Что тестируем: методы add_like и add_view.

        Что передаём: последовательность операций над счётчиками лайков и просмотров.
        Что ожидаем: счётчики увеличиваются в соответствии с операциями.
        """
        highlight = Highlight(
            user_id=1,
            anime_id=7,
            episode=1,
            start_timestamp=5.0,
            end_timestamp=10.0,
        )

        for operation in operations:
            if operation == "like":
                await highlight.add_like()
            else:
                await highlight.add_view()

        assert highlight.likes_count == expected_likes
        assert highlight.views_count == expected_views
