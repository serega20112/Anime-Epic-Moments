from __future__ import annotations

import pytest

from backend.application.use_cases.highlight.get_highlight_comments import GetHighlightCommentsUseCase


@pytest.mark.parametrize(("limit", "expected"), [(1, 1), (500, 100), (12, 12)])
def test_get_highlight_comments_use_case_clamps_limit(limit, expected):
    """Проверяем, что GetHighlightCommentsUseCase ограничивает размер выборки комментариев."""

    class _Repo:
        def __init__(self):
            self.payload = None

        def get_comments(self, **kwargs):
            self.payload = kwargs
            return ["comment"]

    repo = _Repo()
    use_case = GetHighlightCommentsUseCase(repo)

    result = use_case.execute(highlight_id=8, limit=limit)

    assert repo.payload == {"highlight_id": 8, "limit": expected}
    assert result == ["comment"]
