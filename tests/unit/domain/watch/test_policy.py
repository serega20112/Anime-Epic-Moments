from __future__ import annotations

import pytest

from backend.domain.watch.policy import (
    canonicalize_translation_name,
    get_translation_priority,
    is_preferred_translation,
    normalize_translation_name,
)


class TestNormalizeTranslationName:
    """Юнит-тесты нормализации названий озвучек."""

    @pytest.mark.unit
    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            (" Studio-Band ", "studio band"),
            ("AniDUB.TV", "anidub tv"),
            (None, ""),
        ],
    )
    def test_cleans_and_normalizes_input(self, value, expected):
        """Что тестируем: функцию normalize_translation_name.

        Что передаём: названия с лишними пробелами, знаками препинания и None.
        Что ожидаем: строка приводится к нижнему регистру и нормализованному виду, None -> пустая строка.
        """
        assert normalize_translation_name(value) == expected


class TestTranslationPriorityPolicy:
    """Юнит-тесты приоритизации и канонизации групп озвучек."""

    @pytest.mark.unit
    @pytest.mark.parametrize(
        ("value", "expected_label", "preferred"),
        [
            ("студийная банда", "StudioBand", True),
            ("anidub tv", "AniDUB", True),
            ("Custom Fansub", "Custom Fansub", False),
        ],
    )
    def test_priority_and_canonical_name_follow_preferred_groups(
        self,
        value,
        expected_label,
        preferred,
    ):
        """Что тестируем: get_translation_priority, canonicalize_translation_name и is_preferred_translation.

        Что передаём: названия предпочитаемых и обычных озвучек.
        Что ожидаем: для предпочитаемых групп приоритет < 6 и каноническое имя из списка, для прочих - оригинальное имя.
        """
        priority, normalized = get_translation_priority(value)

        assert canonicalize_translation_name(value) == expected_label
        assert is_preferred_translation(value) is preferred
        if preferred:
            assert priority < 6
            assert normalized != ""
        else:
            assert priority >= 6