from __future__ import annotations

from unittest.mock import Mock

import pytest

from src.backend.use_case.watch.add_anime_comment import AddAnimeCommentUseCase


@pytest.mark.parametrize("content", ["", "x", "x" * 601])
def test_add_anime_comment_use_case_rejects_invalid_content(content):
    """Проверяем, что AddAnimeCommentUseCase валидирует длину комментария."""
    use_case = AddAnimeCommentUseCase(Mock())

    with pytest.raises(ValueError):
        use_case.execute(anime_id=7, user_id=4, content=content)


def test_add_anime_comment_use_case_delegates_to_repository():
    """Проверяем, что AddAnimeCommentUseCase передает нормализованный комментарий в репозиторий."""
    repo = Mock()
    repo.add_anime_comment.return_value = "comment"
    use_case = AddAnimeCommentUseCase(repo)

    result = use_case.execute(anime_id=7, user_id=4, content="  Отличный эпизод  ")

    assert result == "comment"
    repo.add_anime_comment.assert_called_once_with(anime_id=7, user_id=4, content="Отличный эпизод")
