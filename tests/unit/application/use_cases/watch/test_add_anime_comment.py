from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from backend.application.dto import AddAnimeCommentCommand
from backend.application.use_cases.watch.discussion.add_anime_comment import (
    AddAnimeCommentUseCase,
)
from tests.support.fakes import FakeUnitOfWork


def _use_case(repository: AsyncMock) -> tuple:
    """Собрать сценарий комментария с двойником репозитория просмотра."""
    uow = FakeUnitOfWork(WatchRepository=repository)
    return AddAnimeCommentUseCase(uow), uow, repository


@pytest.mark.unit
class TestAddAnimeCommentUseCase:
    """Юнит-тесты добавления комментария в обсуждение аниме."""

    async def test_saves_normalized_comment(self):
        """Что тестируем: сохранение комментария с обрезкой пробелов.
        Что передаём: валидный текст с лишними пробелами.
        Что ожидаем: комментарий сохранён зажатым по длине, статус 201.
        """
        repository = AsyncMock()
        repository.add_anime_comment.return_value = {"id": 1}
        use_case, uow, _repository = _use_case(repository)

        result = await use_case.execute(
            AddAnimeCommentCommand(anime_id=7, user_id=3, content="  первая серия  ")
        )

        assert result.ok is True
        assert result.status_code == 201
        assert uow.commits == 1
        repository.add_anime_comment.assert_awaited_once_with(
            anime_id=7, user_id=3, content="первая серия"
        )

    @pytest.mark.parametrize("content", ["", "   ", "a", "a" * 601])
    async def test_rejects_invalid_length(self, content):
        """Что тестируем: границы допустимой длины комментария.
        Что передаём: пустой, односимвольный и слишком длинный текст.
        Что ожидаем: статус 400, комментарий не сохраняется.
        """
        repository = AsyncMock()
        use_case, _uow, _repository = _use_case(repository)

        result = await use_case.execute(
            AddAnimeCommentCommand(anime_id=7, user_id=3, content=content)
        )

        assert result.ok is False
        assert result.status_code == 400
        repository.add_anime_comment.assert_not_awaited()
