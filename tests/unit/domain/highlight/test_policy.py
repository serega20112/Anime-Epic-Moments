from __future__ import annotations

import pytest

from backend.domain.aggregates.highlight.highlight import Highlight
from backend.domain.policies.highlight_policy import HighlightPolicy


class TestHighlightPolicy:
    """Юнит-тесты доменной политики Highlight."""

    @pytest.mark.unit
    @pytest.mark.parametrize(
        ("user_id", "highlights_this_hour", "expected"),
        [
            (None, 4, True),
            (None, 5, False),
            (10, 100, True),
        ],
    )
    async def test_can_add_highlight_applies_guest_limit(
        self,
        user_id,
        highlights_this_hour,
        expected,
    ):
        """Что тестируем: метод can_add_highlight.

        Что передаём: идентификатор пользователя (гость = None) и число хайлайтов за час.
        Что ожидаем: гости ограничены лимитом в час, залогиненные пользователи не ограничены.
        """
        result = await HighlightPolicy.can_add_highlight(user_id, highlights_this_hour)

        assert result is expected

    @pytest.mark.unit
    @pytest.mark.parametrize(
        ("description", "expected"),
        [
            ("красивый момент без спама", False),
            ("очень вредный спам-контент", False),
            ("эмоциональный safe highlight", True),
        ],
    )
    async def test_filter_spoiler_content_filters_banned_words(self, description, expected):
        """Что тестируем: метод filter_spoiler_content.

        Что передаём: описания с запрещёнными маркерами и без них.
        Что ожидаем: безопасное описание возвращает True, содержащее бан-слова — False.
        """
        result = await HighlightPolicy.filter_spoiler_content(description)

        assert result is expected

    @pytest.mark.unit
    @pytest.mark.parametrize("is_spoiler", [False, True])
    async def test_should_hide_spoiler_returns_highlight_flag(self, is_spoiler):
        """Что тестируем: метод should_hide_spoiler.

        Что передаём: Highlight с разным значением is_spoiler.
        Что ожидаем: результат совпадает со значением is_spoiler хайлайта.
        """
        highlight = Highlight(
            user_id=1,
            anime_id=8,
            episode=2,
            start_timestamp=1.0,
            end_timestamp=2.0,
            is_spoiler=is_spoiler,
        )

        assert await HighlightPolicy.should_hide_spoiler(highlight) is is_spoiler
