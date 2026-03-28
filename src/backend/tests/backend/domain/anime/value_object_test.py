from __future__ import annotations

import pytest

from src.backend.domain.anime.value_object import (
    AnimeDiscussionBoard,
    AnimeDiscussionComment,
    SearchAnimeByDescriptionResult,
)


@pytest.mark.parametrize(
    ("requires_age_confirmation", "message"),
    [
        (False, None),
        (True, "Подтвердите возраст"),
    ],
)
def test_search_anime_by_description_result_to_dict_serializes_payload(
    requires_age_confirmation,
    message,
    anime_factory,
):
    """Проверяем, что value object корректно сериализует карточки и age-gate поля."""
    result = SearchAnimeByDescriptionResult(
        items=[anime_factory(external_id="44", title="Result Title")],
        requires_age_confirmation=requires_age_confirmation,
        message=message,
    )

    payload = result.to_dict()

    assert payload["items"][0]["title"] == "Result Title"
    assert payload["requires_age_confirmation"] is requires_age_confirmation
    assert payload["message"] == message


def test_anime_discussion_value_objects_store_comments_and_board():
    """Проверяем, что value objects обсуждения аниме сохраняют комментарии, лайки и сортировку доски."""
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
