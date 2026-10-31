from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from backend.application.dto import SetAnimeCommentLikeCommand
from backend.application.use_cases.watch.discussion.set_anime_comment_like import (
    SetAnimeCommentLikeUseCase,
)
from backend.domain.value_objects.anime.discussion import AnimeDiscussionComment
from tests.support.fakes import FakeUnitOfWork


def _use_case(repository: AsyncMock) -> tuple:
    """Собрать сценарий лайка комментария с двойником репозитория."""
    uow = FakeUnitOfWork(WatchRepository=repository)
    return SetAnimeCommentLikeUseCase(uow), uow, repository


@pytest.mark.unit
class TestSetAnimeCommentLikeUseCase:
    """Юнит-тесты лайка комментария в обсуждении аниме."""

    async def test_returns_updated_comment(self):
        """Что тестируем: постановку лайка и обновлённый комментарий.
        Что передаём: существующий комментарий и команду liked=True.
        Что ожидаем: репозиторий вызван, комментарий с лайком возвращён.
        """
        comment = AnimeDiscussionComment(
            id=4,
            anime_id=7,
            user_id=3,
            username="tester",
            content="отличная серия",
            likes_count=2,
            created_at="2026-03-28",
            is_liked=True,
        )
        repository = AsyncMock()
        repository.set_anime_comment_like.return_value = comment
        use_case, uow, _repository = _use_case(repository)

        result = await use_case.execute(
            SetAnimeCommentLikeCommand(comment_id=4, user_id=3, liked=True)
        )

        assert result.ok is True
        assert result.data is comment
        assert uow.commits == 1
        repository.set_anime_comment_like.assert_awaited_once_with(
            comment_id=4, user_id=3, liked=True
        )

    async def test_returns_not_found_when_comment_missing(self):
        """Что тестируем: отказ при отсутствующем комментарии.
        Что передаём: репозиторий бросает ValueError.
        Что ожидаем: статус 404 с кодом comment_not_found.
        """
        repository = AsyncMock()
        repository.set_anime_comment_like.side_effect = ValueError("нет комментария")
        use_case, _uow, _repository = _use_case(repository)

        result = await use_case.execute(
            SetAnimeCommentLikeCommand(comment_id=999, user_id=3, liked=True)
        )

        assert result.ok is False
        assert result.status_code == 404
        assert result.error == "comment_not_found"
