from __future__ import annotations

from types import SimpleNamespace

import pytest

from backend.presentation.api.v1 import anime_route as anime_route_module
from backend.presentation.api.v1.anime_route import _to_bool, _to_int, anime_bp


@pytest.mark.parametrize(
    ("value", "expected"),
    [("7", 7), ("", None), (None, None), ("abc", None)],
)
def test_anime_route_to_int_parses_expected_values(value, expected):
    """Проверяем, что _to_int корректно обрабатывает валидные и невалидные значения."""
    assert _to_int(value) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [("1", True), ("true", True), ("yes", True), ("0", False), (None, False)],
)
def test_anime_route_to_bool_parses_expected_values(value, expected):
    """Проверяем, что _to_bool корректно распознает булевы query-параметры."""
    assert _to_bool(value) is expected


def test_search_anime_route_serializes_results(flask_app_factory, monkeypatch, anime_factory):
    """Проверяем, что /anime/api/search отдает сериализованные тайтлы из use case."""
    use_case = SimpleNamespace(execute=lambda title, limit: [anime_factory(title="Bleach")])
    monkeypatch.setattr(
        anime_route_module,
        "container",
        SimpleNamespace(search_anime_use_case=lambda: use_case),
    )
    app = flask_app_factory(anime_bp)

    response = app.test_client().get("/anime/api/search?title=Bleach&limit=5")

    assert response.status_code == 200
    assert response.get_json()[0]["title"] == "Bleach"


def test_search_by_description_route_forwards_filters(flask_app_factory, monkeypatch):
    """Проверяем, что /anime/api/search/description передает фильтры в use case без потерь."""
    captured = {}

    class Result:
        def to_dict(self):
            return {"items": [{"title": "Gintama"}]}

    def execute(**kwargs):
        captured.update(kwargs)
        return Result()

    container = SimpleNamespace(
        search_anime_by_description_use_case=lambda: SimpleNamespace(execute=execute)
    )
    monkeypatch.setattr(anime_route_module, "container", container)
    app = flask_app_factory(anime_bp)

    response = app.test_client().get(
        "/anime/api/search/description"
        "?description=comedy&genre_hint=samurai&limit=18&sort=year"
        "&age_rating=18%2B&adult_confirmed=1&year_from=2000&year_to=2020&rating=7"
    )

    assert response.status_code == 200
    assert response.get_json()["items"][0]["title"] == "Gintama"
    assert captured == {
        "description": "comedy",
        "genre_hint": "samurai",
        "year_from": 2000,
        "year_to": 2020,
        "min_rating": 7,
        "age_rating": "18+",
        "adult_confirmed": True,
        "sort_by": "year",
        "limit": 18,
    }
