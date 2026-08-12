from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from backend.application.dto import SetAnimeCommentLikeCommand
from backend.application.use_cases import SetAnimeCommentLikeUseCase


@pytest.mark.unit
class TestSetAnimeCommentLikeUseCase:
    """Юнит-тесты лайка комментария в обсуждении аниме."""

    async def test_delegates_to_repository(self):
        """Что тестируем: передачу флага liked в репозиторий.
        Что передаём: команду с liked=True.
        Что ожидаем: результат успешен, репозиторий вызван корректно.
        """
        repo = AsyncMock()
        repo.set_anime_comment_like.return_value = "comment"
        use_case = SetAnimeCommentLikeUseCase(repo)

        result = await use_case.execute(SetAnimeCommentLikeCommand(comment_id=3, user_id=4, liked=True))

        assert result.ok is True
        assert result.data == "comment"
        repo.set_anime_comment_like.assert_awaited_once_with(
            comment_id=3, user_id=4, liked=True
        )

    async def test_returns_404_when_comment_not_found(self):
        """Что тестируем: обработку отсутствующего комментария.
        Что передаём: репозиторий, бросающий ValueError.
        Что ожидаем: результат failure со статусом 404.
        """
        repo = AsyncMock()
        repo.set_anime_comment_like.side_effect = ValueError("missing")
        use_case = SetAnimeCommentLikeUseCase(repo)

        result = await use_case.execute(SetAnimeCommentLikeCommand(comment_id=99, user_id=4, liked=True))

        assert result.ok is False
        assert result.status_code == 404