from __future__ import annotations

import pytest

from backend.domain.anime.value_object import (
    AnimeDiscussionBoard,
    AnimeDiscussionComment,
    SearchAnimeByDescriptionResult,
)


class TestSearchAnimeByDescriptionResult:
    """Юнит-тесты value object результата поиска аниме по описанию."""

    @pytest.mark.unit
    @pytest.mark.parametrize(
        ("requires_age_confirmation", "message"),
        [
            (False, None),
            (True, "Подтвердите возраст"),
        ],
    )
    async def test_to_dict_serializes_payload(
        self,
        anime_factory,
        requires_age_confirmation,
        message,
    ):
        """Что тестируем: метод to_dict.

        Что передаём: карточки найденного аниме и разные age-gate поля (флаг + сообщение).
        Что ожидаем: словарь содержит title первой карточки и корректные age-gate значения.
        """
        result = SearchAnimeByDescriptionResult(
            items=[anime_factory(external_id="44", title="Result Title")],
            requires_age_confirmation=requires_age_confirmation,
            message=message,
        )

        payload = await result.to_dict()

        assert payload["items"][0]["title"] == "Result Title"
        assert payload["requires_age_confirmation"] is requires_age_confirmation
        assert payload["message"] == message


class TestAnimeDiscussionValueObjects:
    """Юнит-тесты value objects обсуждения аниме."""

    @pytest.mark.unit
    async def test_board_stores_comments_and_sorting(self):
        """Что тестируем: value objects AnimeDiscussionComment и AnimeDiscussionBoard.

        Что передаём: комментарий с данными пользователя и доску обсуждения с сортировкой.
        Что ожидаем: комментарий и доска сохраняют переданные поля и сортировку.
        """
        comment = AnimeDiscussionComment(
            id=1,
            anime_id=7,
            user_id=4,
            username="tester",
            content="Очень сильный эпизод",
            likes_count=3,
            created_at="2026-03-28 22:00",
            is_liked=True,
        )
        board = AnimeDiscussionBoard(
            anime_id=7,
            items=[comment],
            selected_sort="popular",
            total_comments=1,
        )

        assert board.items[0].username == "tester"
        assert board.items[0].likes_count == 3
        assert board.selected_sort == "popular"
