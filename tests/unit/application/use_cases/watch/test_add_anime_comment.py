from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from backend.application.dto import AddAnimeCommentCommand
from backend.application.use_cases.watch.discussion.add_anime_comment import AddAnimeCommentUseCase


@pytest.mark.unit
class TestAddAnimeCommentUseCase:
    """Юнит-тесты добавления комментария к обсуждению аниме."""

    @pytest.mark.parametrize("content", ["", "x", "x" * 601])
    async def test_rejects_invalid_content(self, content):
        """Что тестируем: валидацию длины комментария.
        Что передаём: пустой, слишком короткий и слишком длинный контент.
        Что ожидаем: результат failure со статусом 400, репозиторий не вызывается.
        """
        repo = AsyncMock()
        use_case = AddAnimeCommentUseCase(repo, AsyncMock())

        result = await use_case.execute(
            AddAnimeCommentCommand(anime_id=7, user_id=4, content=content)
        )

        assert result.ok is False
        assert result.status_code == 400
        repo.add_anime_comment.assert_not_awaited()

    async def test_delegates_to_repository(self):
        """Что тестируем: передачу нормализованного комментария в репозиторий.
        Что передаём: контент с лишними пробелами.
        Что ожидаем: результат успешен, репозиторий вызван с обрезанным контентом.
        """
        repo = AsyncMock()
        repo.add_anime_comment.return_value = "comment"
        use_case = AddAnimeCommentUseCase(repo, AsyncMock())

        result = await use_case.execute(
            AddAnimeCommentCommand(anime_id=7, user_id=4, content="  Отличный эпизод  ")
        )

        assert result.ok is True
        assert result.status_code == 201
        assert result.data == "comment"
        repo.add_anime_comment.assert_awaited_once_with(
            anime_id=7, user_id=4, content="Отличный эпизод"
        )
