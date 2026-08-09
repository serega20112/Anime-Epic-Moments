from __future__ import annotations

import pytest

from backend.application.use_cases.highlight.get_highlight_likers import GetHighlightLikersUseCase


@pytest.mark.parametrize(("limit", "expected"), [(2, 2), (500, 100), (17, 17)])
def test_get_highlight_likers_use_case_clamps_limit(limit, expected):
    """Проверяем, что GetHighlightLikersUseCase ограничивает размер выборки лайкнувших пользователей."""

    class _Repo:
        def __init__(self):
            self.payload = None

        def get_likers(self, **kwargs):
            self.payload = kwargs
            return ["liker"]

    repo = _Repo()
    use_case = GetHighlightLikersUseCase(repo)

    result = use_case.execute(highlight_id=8, limit=limit)

    assert repo.payload == {"highlight_id": 8, "limit": expected}
    assert result == ["liker"]
