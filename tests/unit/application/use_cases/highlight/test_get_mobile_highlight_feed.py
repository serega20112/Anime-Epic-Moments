from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock

import pytest

from backend.application.dto.highlight import MobileHighlightFeedQuery
from backend.application.use_cases.highlight.feed.get_mobile_highlight_feed import (
    GetMobileHighlightFeedUseCase,
)
from backend.domain import Highlight
from backend.domain.entities.anime.anime import Anime
from tests.support.fakes import FakeUnitOfWork


def _highlight(highlight_id: int) -> Highlight:
    """Собрать хайлайт с указанным идентификатором и одинаковой меткой времени.

    created_at задаётся явно и одинаково для всех карточек, чтобы порядок в
    режиме top был детерминирован только по лайкам, а не по наносекундам
    создания фейковых объектов.
    """
    highlight = Highlight(
        user_id=3,
        anime_id=7,
        episode=1,
        start_timestamp=10.0,
        end_timestamp=40.0,
        title="Момент",
        created_at=datetime(2024, 1, 1),
    )
    highlight.id = highlight_id
    highlight.likes_count = 2
    highlight.views_count = 5
    return highlight


def _use_case(top_highlights, recent_highlights, liked_highlights):
    """Собрать сценарий мобильной ленты с двойниками репозиториев и каталога."""
    highlight_repository = AsyncMock()
    highlight_repository.get_public_top.return_value = top_highlights
    highlight_repository.get_public_recent.return_value = recent_highlights
    highlight_repository.get_liked_by_user.return_value = liked_highlights
    highlight_repository.get_engagement_map.return_value = {}
    user_repository = AsyncMock()
    user_repository.get_by_ids.return_value = []
    anime = Anime(external_id="7", title="Gintama", genres=["Comedy"], episode_count=2)
    client = AsyncMock()
    client.get_by_id.return_value = anime
    uow = FakeUnitOfWork(HighlightRepository=highlight_repository, UserRepository=user_repository)
    return GetMobileHighlightFeedUseCase(uow, client), highlight_repository


@pytest.mark.unit
class TestGetMobileHighlightFeedUseCase:
    """Юнит-тесты режимов и пагинации мобильной ленты хайлайтов."""

    async def test_top_mode_returns_cards_and_navigation(self):
        """Что тестируем: режим top с одной страницей карточек.
        Что передаём: два топовых хайлайта и размер страницы один.
        Что ожидаем: первая страница содержит один хайлайт, total два, есть следующая.
        """
        use_case, _repo = _use_case([_highlight(1), _highlight(2)], [], [])

        page = await use_case.execute(MobileHighlightFeedQuery(mode="top", page=1, per_page=1))

        assert [card.id for card in page.items] == [1]
        assert page.total == 2
        assert page.total_pages == 2
        assert page.has_next is True
        assert page.has_previous is False

    async def test_second_page_slices_window(self):
        """Что тестируем: вторую страницу режима top.
        Что передаём: те же два хайлайта, страницу два при размере один.
        Что ожидаем: возвращается второй хайлайт, следующей страницы нет.
        """
        use_case, _repo = _use_case([_highlight(1), _highlight(2)], [], [])

        page = await use_case.execute(MobileHighlightFeedQuery(mode="top", page=2, per_page=1))

        assert [card.id for card in page.items] == [2]
        assert page.has_next is False
        assert page.has_previous is True

    async def test_guest_for_you_mode_uses_recent_without_likes(self):
        """Что тестируем: режим for_you для гостя.
        Что передаём: свежие хайлайты и отсутствующего зрителя.
        Что ожидаем: лайкнутые не запрашиваются, отдаются свежие карточки.
        """
        use_case, highlight_repository = _use_case([], [_highlight(9)], [])

        page = await use_case.execute(
            MobileHighlightFeedQuery(mode="for_you", page=1, per_page=10, viewer_user_id=None)
        )

        assert [card.id for card in page.items] == [9]
        highlight_repository.get_liked_by_user.assert_not_awaited()
