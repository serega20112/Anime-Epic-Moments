from __future__ import annotations

import pytest

from src.backend.domain.anime.value_object import SearchAnimeByDescriptionResult


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
