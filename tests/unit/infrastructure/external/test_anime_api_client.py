from __future__ import annotations

from unittest.mock import AsyncMock

import httpx
import pytest

from backend.infrastructure.external import AnimeApiClient


def _response(payload, status_code: int = 200, method: str = "GET"):
    return httpx.Response(
        status_code,
        json=payload,
        request=httpx.Request(method, "http://testserver/"),
    )


@pytest.mark.unit
@pytest.mark.parametrize("include_adult", [False, True])
async def test_search_by_title_uses_cache_for_repeated_queries(include_adult):
    """Проверяем, что повторный title-поиск не делает второй сетевой запрос."""
    client = AnimeApiClient()
    client.session.get = AsyncMock(
        return_value=_response(
            {
                "data": [
                    {
                        "mal_id": 5114,
                        "title": "Fullmetal Alchemist: Brotherhood",
                        "synopsis": "desc",
                        "genres": [{"name": "Action"}],
                        "episodes": 64,
                        "year": 2009,
                        "score": 9.1,
                        "images": {"jpg": {"image_url": "cover"}},
                        "rating": "PG-13",
                    }
                ]
            }
        )
    )

    first = await client.search_by_title("FMA", limit=5, include_adult=include_adult)
    second = await client.search_by_title("FMA", limit=5, include_adult=include_adult)

    assert client.session.get.await_count == 1
    assert [item.title for item in first] == [item.title for item in second]
    assert first[0].episode_count == 64


@pytest.mark.unit
async def test_get_by_id_caches_fallback_result(anime_factory):
    """Проверяем, что fallback по AniList для get_by_id тоже кэшируется."""
    client = AnimeApiClient()
    error_response = httpx.Response(
        404,
        request=httpx.Request("GET", f"{client.jikan_base}/anime/918"),
    )
    client.session.get = AsyncMock(
        side_effect=httpx.HTTPStatusError(
            "404", request=error_response.request, response=error_response
        )
    )
    client._get_by_anilist_id = AsyncMock(
        return_value=anime_factory(external_id="918", title="Gintama")
    )

    first = await client.get_by_id(918)
    second = await client.get_by_id(918)

    assert client.session.get.await_count == 1
    assert client._get_by_anilist_id.await_count == 1
    assert first.title == second.title == "Gintama"


@pytest.mark.unit
@pytest.mark.parametrize(
    ("filters", "expected_call_count"),
    [
        ({"year_from": 2010, "year_to": 2020, "min_rating": 7}, 1),
        ({"year_from": None, "year_to": None, "min_rating": None}, 1),
    ],
)
async def test_search_by_description_uses_cache_with_filter_signature(filters, expected_call_count):
    """Проверяем, что одинаковый набор фильтров переиспользует кэш поиска по описанию."""
    client = AnimeApiClient()
    client.session.post = AsyncMock(
        return_value=_response(
            {
                "data": {
                    "Page": {
                        "media": [
                            {
                                "id": 1,
                                "idMal": 20,
                                "title": {
                                    "romaji": "Naruto",
                                    "english": "Naruto",
                                    "native": "ナルト",
                                },
                                "description": "desc",
                                "genres": ["Action"],
                                "isAdult": False,
                                "seasonYear": 2002,
                                "averageScore": 79,
                                "coverImage": {"large": "cover"},
                            }
                        ]
                    }
                }
            }
        )
    )

    first = await client.search_by_description("ninja", limit=8, **filters)
    second = await client.search_by_description("ninja", limit=8, **filters)

    assert client.session.post.await_count == expected_call_count
    assert [item.external_id for item in first] == [item.external_id for item in second]
