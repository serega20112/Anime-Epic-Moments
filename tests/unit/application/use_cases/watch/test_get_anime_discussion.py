from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from backend.application.dto import AnimeDiscussionQuery
from backend.application.use_cases import GetAnimeDiscussionUseCase
from backend.domain.value_objects.anime.discussion import AnimeDiscussionComment
from tests.support.fakes import FakeUnitOfWork


def _comment(comment_id: int) -> AnimeDiscussionComment:
    """Собрать комментарий обсуждения с указанным идентификатором."""
    return AnimeDiscussionComment(
        id=comment_id,
        anime_id=7,
        user_id=3,
        username="tester",
        content="обсуждение серии",
        likes_count=1,
        created_at="2026-03-28",
    )


def _use_case(repository: AsyncMock) -> tuple:
    """Собрать сценарий чтения обсуждения с двойником репозитория."""
    uow = FakeUnitOfWork(WatchRepository=repository)
    return GetAnimeDiscussionUseCase(uow), uow, repository


@pytest.mark.unit
class TestGetAnimeDiscussionUseCase:
    """Юнит-тесты чтения обсуждения аниме."""

    async def test_normalizes_sort_and_counts_comments(self):
        """Что тестируем: нормализацию сортировки и подсчёт комментариев.
        Что передаём: неизвестный sort_by и два комментария от репозитория.
        Что ожидаем: сортировка сведена к popular, счётчик равен числу комментариев.
        """
        repository = AsyncMock()
        repository.get_anime_comments.return_value = [_comment(1), _comment(2)]
        use_case, uow, _repository = _use_case(repository)

        result = await use_case.execute(
            AnimeDiscussionQuery(anime_id=7, sort_by="top", viewer_user_id=3, limit=5)
        )

        assert result.ok is True
        assert uow.commits == 1
        repository.get_anime_comments.assert_awaited_once_with(
            anime_id=7, sort_by="popular", viewer_user_id=3, limit=5
        )
        board = result.data
        assert board.total_comments == 2
        assert board.selected_sort == "popular"
        assert board.anime_id == 7

    async def test_keeps_recent_sort(self):
        """Что тестируем: сохранение допустимой сортировки по свежести.
        Что передаём: sort_by='recent'.
        Что ожидаем: репозиторий вызван с той же сортировкой.
        """
        repository = AsyncMock()
        repository.get_anime_comments.return_value = []
        use_case, _uow, _repository = _use_case(repository)

        result = await use_case.execute(AnimeDiscussionQuery(anime_id=7, sort_by="RECENT "))

        repository.get_anime_comments.assert_awaited_once_with(
            anime_id=7, sort_by="recent", viewer_user_id=None, limit=20
        )
        assert result.data.selected_sort == "recent"

    async def test_returns_empty_board_on_repository_failure(self):
        """Что тестируем: устойчивость страницы к сбою чтения обсуждения.
        Что передаём: репозиторий бросает исключение.
        Что ожидаем: результат успешен с пустой доской выбранной сортировки.
        """
        repository = AsyncMock()
        repository.get_anime_comments.side_effect = RuntimeError("база недоступна")
        use_case, _uow, _repository = _use_case(repository)

        result = await use_case.execute(AnimeDiscussionQuery(anime_id=7, sort_by="popular"))

        assert result.ok is True
        assert result.data.items == []
        assert result.data.total_comments == 0
