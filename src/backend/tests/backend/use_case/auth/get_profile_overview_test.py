from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace
from unittest.mock import Mock

from src.backend.domain.highlight.value_object import HighlightProfileSummary
from src.backend.domain.user.entity import User
from src.backend.use_case.auth.get_profile_overview import GetProfileOverviewUseCase


def test_get_profile_overview_use_case_builds_profile_sections(monkeypatch):
    """Проверяем, что GetProfileOverviewUseCase собирает статистику, подборки и social-активность для профиля."""
    user_repo = Mock()
    user_repo.get_by_id.return_value = User(
        id=4,
        email="user@example.com",
        username="tester",
        password_hash="hash",
        avatar_url="https://example.com/avatar.png",
        created_at=datetime(2026, 3, 20),
    )
    highlight_repo = Mock()
    highlight_repo.get_profile_summary.return_value = HighlightProfileSummary(
        highlight_count=3,
        like_count=5,
        saved_count=7,
    )
    highlight_repo.get_recent_activity.return_value = [SimpleNamespace(action="like")]
    use_case = GetProfileOverviewUseCase(user_repo, highlight_repo, Mock())

    use_case.recent_highlights_use_case = SimpleNamespace(
        execute=lambda **kwargs: SimpleNamespace(items=["recent-1", "recent-2", "recent-3", "recent-4", "recent-5"])
    )
    use_case.liked_highlights_use_case = SimpleNamespace(
        execute=lambda **kwargs: SimpleNamespace(items=["liked-1", "liked-2"])
    )
    use_case.saved_highlights_use_case = SimpleNamespace(
        execute=lambda **kwargs: SimpleNamespace(items=["saved-1", "saved-2"])
    )

    overview = use_case.execute(4)

    assert overview.summary.saved_count == 7
    assert overview.recent_highlights == ["recent-1", "recent-2", "recent-3", "recent-4"]
    assert overview.popular_highlights == ["recent-1", "recent-2", "recent-3", "recent-4"]
    assert overview.liked_highlights == ["liked-1", "liked-2"]
    assert overview.saved_highlights == ["saved-1", "saved-2"]
    assert overview.recent_activity[0].action == "like"
