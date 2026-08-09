from __future__ import annotations

from unittest.mock import Mock

import pytest

from backend.application.use_cases.highlight.create_highlight import CreateHighlightUseCase


@pytest.mark.parametrize(
    ("user_id", "highlights_this_hour", "should_invalidate"),
    [(1, 0, True), (None, 0, False)],
)
def test_create_highlight_use_case_persists_highlight_and_invalidates_cache(
        user_id,
        highlights_this_hour,
        should_invalidate,
):
    """Проверяем, что create_highlight сохраняет хайлайт и инвалидирует рекомендации только для авторизованного пользователя."""
    repo = Mock()
    repo.add.side_effect = lambda highlight: highlight
    recommendation_service = Mock()
    use_case = CreateHighlightUseCase(repo, recommendation_service)

    result = use_case.execute(
        user_id=user_id,
        anime_id=18,
        episode=1,
        start_timestamp=10.0,
        end_timestamp=25.0,
        description="epic drift",
        is_spoiler=False,
        emotion="hype",
        highlights_this_hour=highlights_this_hour,
    )

    assert result.description == "epic drift"
    repo.add.assert_called_once()
    assert recommendation_service.invalidate_user.call_count == int(should_invalidate)


@pytest.mark.parametrize(
    ("description", "expected_exception"),
    [("мат", ValueError), ("спам", ValueError)],
)
def test_create_highlight_use_case_rejects_blocked_content(description, expected_exception):
    """Проверяем, что create_highlight не пропускает запрещенное описание."""
    use_case = CreateHighlightUseCase(Mock(), Mock())

    with pytest.raises(expected_exception):
        use_case.execute(
            user_id=1,
            anime_id=18,
            episode=1,
            start_timestamp=10.0,
            end_timestamp=20.0,
            description=description,
        )
