"""Регрессионные тесты трансформации ответа Kodik в карту доступности серий."""

import pytest

from backend.infrastructure.external.mapping.kodik import map_kodik_translations_to_episodes

pytestmark = pytest.mark.unit


def _material(translation_id: int, title: str, seasons: dict | None = None, **extra) -> dict:
    material = {
        "id": f"mat-{translation_id}",
        "link": "//kodik.info/serial/123/abc/720p",
        "translation": {"id": translation_id, "title": title, "type": "voice"},
    }
    if seasons is not None:
        material["seasons"] = seasons
    material.update(extra)
    return material


class TestMapKodikTranslationsToEpisodes:
    def test_isolates_episodes_per_translation(self):
        payload = {
            "results": [
                _material(
                    609,
                    "AniLibria.TV",
                    seasons={"1": {"episodes": {str(n): f"link{n}" for n in range(1, 9)}}},
                ),
                _material(
                    610,
                    "Studio Band",
                    seasons={"1": {"episodes": {str(n): f"link{n}" for n in range(1, 6)}}},
                ),
            ]
        }
        result = map_kodik_translations_to_episodes(payload)
        assert len(result) == 2
        by_id = {item.translation_id: item for item in result}
        assert by_id[609].episodes_count == 8
        assert by_id[609].available_episodes == list(range(1, 9))
        assert by_id[610].episodes_count == 5
        assert by_id[610].available_episodes == list(range(1, 6))

    def test_no_global_counter_leak(self):
        payload = {
            "results": [
                _material(
                    1, "Full", seasons={"1": {"episodes": {str(n): "l" for n in range(1, 13)}}}
                ),
                _material(2, "Partial", seasons={"1": {"episodes": {"1": "l", "2": "l"}}}),
            ]
        }
        result = map_kodik_translations_to_episodes(payload)
        partial = next(item for item in result if item.translation_id == 2)
        assert partial.available_episodes == [1, 2]
        assert partial.episodes_count == 2

    def test_range_fallback_without_seasons(self):
        payload = {
            "results": [
                _material(7, "Range", first_episode=3, last_episode=5),
            ]
        }
        result = map_kodik_translations_to_episodes(payload)
        assert result[0].available_episodes == [3, 4, 5]

    def test_movie_counts_as_episode_one(self):
        payload = {"results": [_material(9, "Movie")]}
        result = map_kodik_translations_to_episodes(payload)
        assert result[0].available_episodes == [1]

    def test_skips_broken_translation_ids(self):
        payload = {
            "results": [
                {"translation": {"id": None, "title": "Bad"}, "seasons": {}},
                _material(5, "Good", seasons={"1": {"episodes": {"1": "l"}}}),
            ]
        }
        result = map_kodik_translations_to_episodes(payload)
        assert [item.translation_id for item in result] == [5]

    def test_empty_and_invalid_payloads(self):
        assert map_kodik_translations_to_episodes(None) == []
        assert map_kodik_translations_to_episodes({}) == []
        assert map_kodik_translations_to_episodes({"results": []}) == []
        assert map_kodik_translations_to_episodes({"results": "nope"}) == []

    def test_subtitle_type_normalized(self):
        payload = {
            "results": [
                {
                    "translation": {"id": 3, "title": "Subs", "type": "subtitles"},
                    "seasons": {"1": {"episodes": {"1": "l"}}},
                }
            ]
        }
        result = map_kodik_translations_to_episodes(payload)
        assert result[0].translation_type == "sub"

    def test_has_episode_check(self):
        payload = {
            "results": [
                _material(1, "A", seasons={"1": {"episodes": {"1": "l", "2": "l"}}}),
            ]
        }
        result = map_kodik_translations_to_episodes(payload)
        assert result[0].has_episode(2) is True
        assert result[0].has_episode(3) is False
