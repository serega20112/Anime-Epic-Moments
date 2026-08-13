from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from backend.application.use_cases.favorite.add_favorite import AddFavoriteUseCase


@pytest.mark.parametrize(
    ("genres_input", "expected_genres"),
    [
        ([" Action ", "Comedy"], ["Action", "Comedy"]),
        ('["Drama", " Mystery "]', ["Drama", "Mystery"]),
        ("Action, Comedy", ["Action", "Comedy"]),
    ],
)
async def test_add_favorite_use_case_normalizes_payload_and_invalidates_cache(
        genres_input,
        expected_genres,
):
    """Проверяем, что add_favorite нормализует snapshot-данные и сбрасывает рекомендации."""
    repo = AsyncMock()
    recommendation_service = AsyncMock()
    profile_cache = AsyncMock()
    use_case = AddFavoriteUseCase(repo, AsyncMock(), recommendation_service, profile_cache)
    repo.add.side_effect = lambda favorite: favorite

    result = await use_case.execute(
        user_id="5",
        anime_id="10",
        title="  Initial D  ",
        description="  street racing  ",
        cover_url="  https://example.com/cover.jpg  ",
        genres=genres_input,
    )

    assert result.user_id == 5
    assert result.anime_id == 10
    assert result.title == "Initial D"
    assert result.description == "street racing"
    assert result.cover_url == "https://example.com/cover.jpg"
    assert result.genres == expected_genres
    recommendation_service.invalidate_user.assert_called_once_with(5)
    profile_cache.invalidate_user.assert_called_once_with(5, include_ai_summary=True)
