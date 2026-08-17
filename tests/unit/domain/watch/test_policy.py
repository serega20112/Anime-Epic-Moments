from __future__ import annotations

import pytest

from backend.domain.watch.policy import (
    PREFERRED_TRANSLATION_GROUPS,
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
    async def test_cleans_and_normalizes_input(self, value, expected):
        """Что тестируем: функцию normalize_translation_name.

        Что передаём: названия с лишними пробелами, знаками препинания и None.
        Что ожидаем: строка приводится к нижнему регистру и нормализованному виду,
        None -> пустая строка.
        """
        assert await normalize_translation_name(value) == expected


class TestTranslationPriorityPolicy:
    """Юнит-тесты приоритизации и канонизации групп озвучек."""

    @pytest.mark.unit
    @pytest.mark.parametrize(
        ("value", "expected_label", "preferred"),
        [
            ("студийная банда", "StudioBand", True),
            ("anidub tv", "AniDUB", True),
            ("комната диди", "Komnata Didi", True),
            ("didi", "Komnata Didi", True),
            ("sovetromantica", "SovetRomantica", True),
            ("Custom Fansub", "Custom Fansub", False),
        ],
    )
    async def test_priority_and_canonical_name_follow_preferred_groups(
        self,
        value,
        expected_label,
        preferred,
    ):
        """Что тестируем: get_translation_priority, canonicalize и is_preferred_translation.

        Что передаём: названия предпочитаемых и обычных озвучек.
        Что ожидаем: для предпочитаемых групп приоритет меньше длины списка предпочитаемых групп
        и каноническое имя из списка, для прочих - оригинальное имя.
        """
        priority, normalized = await get_translation_priority(value)

        assert await canonicalize_translation_name(value) == expected_label
        assert await is_preferred_translation(value) is preferred
        if preferred:
            assert priority < len(PREFERRED_TRANSLATION_GROUPS)
            assert normalized != ""
        else:
            assert priority >= len(PREFERRED_TRANSLATION_GROUPS)
