from __future__ import annotations

from unittest.mock import Mock

import pytest

from backend.application.use_cases import DeleteHighlightUseCase
from backend.domain import Highlight


def test_delete_highlight_use_case_removes_highlight_and_invalidates_cache():
    """Проверяем, что delete_highlight удаляет найденный хайлайт и очищает рекомендации пользователя."""
    repo = Mock()
    recommendation_service = Mock()
    highlight = Highlight(
        user_id=8,
        anime_id=1,
        episode=1,
        start_timestamp=1.0,
        end_timestamp=2.0,
        description="desc",
    )
    highlight.id = 55
    repo.get_by_id.return_value = highlight
    use_case = DeleteHighlightUseCase(repo, recommendation_service)

    use_case.execute(55)

    repo.delete.assert_called_once_with(55)
    recommendation_service.invalidate_user.assert_called_once_with(8)


@pytest.mark.parametrize("highlight_id", [1, 77])
def test_delete_highlight_use_case_raises_for_missing_item(highlight_id):
    """Проверяем, что delete_highlight сообщает об отсутствии хайлайта."""
    repo = Mock()
    repo.get_by_id.return_value = None
    use_case = DeleteHighlightUseCase(repo, Mock())

    with pytest.raises(ValueError):
        use_case.execute(highlight_id)

    repo.delete.assert_not_called()
