from __future__ import annotations

import pytest

from src.backend.domain.watch.policy import (
    canonicalize_translation_name,
    get_translation_priority,
    is_preferred_translation,
    normalize_translation_name,
)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (" Studio-Band ", "studio band"),
        ("AniDUB.TV", "anidub tv"),
        (None, ""),
    ],
)
def test_normalize_translation_name_cleans_input(value, expected):
    """Проверяем, что normalize_translation_name приводит названия озвучек к каноническому виду."""
    assert normalize_translation_name(value) == expected


@pytest.mark.parametrize(
    ("value", "expected_label", "preferred"),
    [
        ("студийная банда", "StudioBand", True),
        ("anidub tv", "AniDUB", True),
        ("Custom Fansub", "Custom Fansub", False),
    ],
)
def test_translation_priority_and_canonical_name_follow_preferred_groups(
    value,
    expected_label,
    preferred,
):
    """Проверяем, что policy определяет приоритет и каноническое имя предпочитаемых озвучек."""
    priority, normalized = get_translation_priority(value)

    assert canonicalize_translation_name(value) == expected_label
    assert is_preferred_translation(value) is preferred
    if preferred:
        assert priority < 6
        assert normalized != ""
    else:
        assert priority >= 6
