from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from backend.application.use_cases import GetAnimeDiscussionUseCase


@pytest.mark.unit
class TestGetAnimeDiscussionUseCase:
    """Юнит-тесты сборки доски обсуждения аниме."""

    async def test_normalizes_sort_and_builds_board(self):
        """Что тестируем: нормализацию сортировки и сборку доски.
        Что передаём: неизвестную сортировку и два комментария.
        Что ожидаем: selected_sort=popular, total_comments=2, репозиторий вызван корректно.
        """
        repo = AsyncMock()
        repo.get_anime_comments.return_value = ["comment-1", "comment-2"]
        use_case = GetAnimeDiscussionUseCase(repo)

        result = await use_case.execute(
            anime_id=7, sort_by="unknown", viewer_user_id=4, limit=10
        )

        assert result.ok is True
        assert result.data.selected_sort == "popular"
        assert result.data.total_comments == 2
        repo.get_anime_comments.assert_awaited_once_with(
            anime_id=7,
            sort_by="popular",
            viewer_user_id=4,
            limit=10,
        )

    async def test_returns_empty_board_on_error(self):
        """Что тестируем: fallback на пустую доску при ошибке репозитория.
        Что передаём: репозиторий, бросающий исключение.
        Что ожидаем: успешный результат с пустым списком и total=0.
        """
        repo = AsyncMock()
        repo.get_anime_comments.side_effect = ValueError("boom")
        use_case = GetAnimeDiscussionUseCase(repo)

        result = await use_case.execute(anime_id=7, sort_by="recent", limit=10)

        assert result.ok is True
        assert result.data.items == []
        assert result.data.total_comments == 0