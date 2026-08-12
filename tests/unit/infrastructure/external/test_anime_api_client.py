from __future__ import annotations

from unittest.mock import Mock

import pytest
import requests

from backend.infrastructure.external import AnimeApiClient


class FakeResponse:
    def __init__(self, payload, status_code: int = 200):
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(response=self)

    def json(self):
        return self._payload


@pytest.mark.unit
@pytest.mark.parametrize("include_adult", [False, True])
async def test_search_by_title_uses_cache_for_repeated_queries(include_adult):
    """Проверяем, что повторный title-поиск не делает второй сетевой запрос."""
    client = AnimeApiClient()
    client.session.get = Mock(
        return_value=FakeResponse(
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

    assert client.session.get.call_count == 1
    assert [item.title for item in first] == [item.title for item in second]
    assert first[0].episode_count == 64


@pytest.mark.unit
async def test_get_by_id_caches_fallback_result(anime_factory):
    """Проверяем, что fallback по AniList для get_by_id тоже кэшируется."""
    client = AnimeApiClient()
    client.session.get = Mock(side_effect=requests.HTTPError(response=FakeResponse({}, 404)))
    client._get_by_anilist_id = Mock(return_value=anime_factory(external_id="918", title="Gintama"))

    first = await client.get_by_id(918)
    second = await client.get_by_id(918)

    assert client.session.get.call_count == 1
    assert client._get_by_anilist_id.call_count == 1
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
    client.session.post = Mock(
        return_value=FakeResponse(
            {
                "data": {
                    "Page": {
                        "media": [
                            {
                                "id": 1,
                                "idMal": 20,
                                "title": {"romaji": "Naruto", "english": "Naruto", "native": "ナルト"},
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

    assert client.session.post.call_count == expected_call_count
    assert [item.external_id for item in first] == [item.external_id for item in second]
