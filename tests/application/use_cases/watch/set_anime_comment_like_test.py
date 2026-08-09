from __future__ import annotations

from unittest.mock import Mock

from backend.application.use_cases import SetAnimeCommentLikeUseCase


def test_set_anime_comment_like_use_case_delegates_to_repository():
    """Проверяем, что SetAnimeCommentLikeUseCase передает флаг liked в репозиторий."""
    repo = Mock()
    repo.set_anime_comment_like.return_value = "comment"
    use_case = SetAnimeCommentLikeUseCase(repo)

    result = use_case.execute(comment_id=3, user_id=4, liked=True)

    assert result == "comment"
    repo.set_anime_comment_like.assert_called_once_with(comment_id=3, user_id=4, liked=True)
