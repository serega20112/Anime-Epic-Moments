from __future__ import annotations

from unittest.mock import Mock

from src.backend.use_case.highlight.set_saved_highlight import SetSavedHighlightUseCase


def test_set_saved_highlight_use_case_delegates_to_repository():
    """Проверяем, что SetSavedHighlightUseCase делегирует сохранение хайлайта в репозиторий."""
    repo = Mock()
    repo.set_saved.return_value = True
    use_case = SetSavedHighlightUseCase(repo)

    result = use_case.execute(highlight_id=4, user_id=3, saved=True)

    repo.set_saved.assert_called_once_with(highlight_id=4, user_id=3, saved=True)
    assert result is True
