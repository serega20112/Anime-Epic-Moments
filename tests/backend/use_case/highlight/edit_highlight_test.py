from __future__ import annotations

from unittest.mock import Mock

import pytest

from src.backend.domain.highlight.entity import Highlight
from src.backend.use_case.highlight.edit_highlight import EditHighlightUseCase


def test_edit_highlight_use_case_updates_highlight_and_invalidates_cache():
    """Проверяем, что edit_highlight обновляет запись и сбрасывает рекомендации пользователя."""
    repo = Mock()
    recommendation_service = Mock()
    highlight = Highlight(
        user_id=3,
        anime_id=18,
        episode=1,
        start_timestamp=5.0,
        end_timestamp=10.0,
        description="before",
        is_spoiler=False,
    )
    highlight.id = 44
    repo.get_by_id.return_value = highlight
    repo.update.side_effect = lambda item: item
    use_case = EditHighlightUseCase(repo, recommendation_service)

    result = use_case.execute(
        highlight_id=44,
        episode=2,
        start_timestamp=15.0,
        end_timestamp=25.0,
        description="after",
        is_spoiler=True,
        emotion="shock",
    )

    assert result.episode == 2
    assert result.description == "after"
    assert result.is_spoiler is True
    recommendation_service.invalidate_user.assert_called_once_with(3)


@pytest.mark.parametrize("description", ["мат", "спам"])
def test_edit_highlight_use_case_rejects_blocked_description(description):
    """Проверяем, что edit_highlight блокирует запрещенное описание до обновления записи."""
    repo = Mock()
    repo.get_by_id.return_value = Highlight(
        user_id=1,
        anime_id=18,
        episode=1,
        start_timestamp=5.0,
        end_timestamp=10.0,
        description="before",
    )
    use_case = EditHighlightUseCase(repo, Mock())

    with pytest.raises(ValueError):
        use_case.execute(
            highlight_id=1,
            episode=1,
            start_timestamp=5.0,
            end_timestamp=10.0,
            description=description,
            is_spoiler=False,
        )

    repo.update.assert_not_called()
