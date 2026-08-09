from __future__ import annotations

import pytest

from backend.application.use_cases.highlight.get_highlight_notifications import GetHighlightNotificationsUseCase


@pytest.mark.parametrize(("limit", "expected"), [(1, 1), (500, 100), (20, 20)])
def test_get_highlight_notifications_use_case_clamps_limit(limit, expected):
    """Проверяем, что GetHighlightNotificationsUseCase ограничивает размер выборки уведомлений."""

    class _Repo:
        def __init__(self):
            self.payload = None

        def get_recent_activity(self, **kwargs):
            self.payload = kwargs
            return ["notification"]

    repo = _Repo()
    use_case = GetHighlightNotificationsUseCase(repo)

    result = use_case.execute(user_id=8, limit=limit)

    assert repo.payload == {"user_id": 8, "limit": expected}
    assert result == ["notification"]
