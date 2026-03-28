from __future__ import annotations

from unittest.mock import Mock

from src.backend.use_case.watch.get_anime_discussion import GetAnimeDiscussionUseCase


def test_get_anime_discussion_use_case_normalizes_sort_and_builds_board():
    """Проверяем, что GetAnimeDiscussionUseCase собирает доску обсуждения с нормализованной сортировкой."""
    repo = Mock()
    repo.get_anime_comments.return_value = ["comment-1", "comment-2"]
    use_case = GetAnimeDiscussionUseCase(repo)

    result = use_case.execute(anime_id=7, sort_by="unknown", viewer_user_id=4, limit=10)

    assert result.selected_sort == "popular"
    assert result.total_comments == 2
    repo.get_anime_comments.assert_called_once_with(
        anime_id=7,
        sort_by="popular",
        viewer_user_id=4,
        limit=10,
    )
