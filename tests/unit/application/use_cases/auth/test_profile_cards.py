from __future__ import annotations

from datetime import UTC, datetime

import pytest

from backend.application.use_cases.auth.profile.profile_cards import (
    average_catalog_rating,
    build_rating_cards,
    build_recent_episode_cards,
    build_top_anime,
    collect_genres,
    cover_of,
    original_title_of,
    title_of,
)
from backend.domain import Favorite, UserAnimeRating, ViewingSession
from backend.domain.entities.anime.anime import Anime

MOMENT = datetime(2026, 3, 28, 12, 0, tzinfo=UTC)


@pytest.mark.unit
class TestProfileCards:
    """Юнит-тесты сборки карточек профиля из карточек каталога."""

    def test_collect_genres_prefers_stored_snapshot_then_catalog(self):
        """Что тестируем: источник жанров для анализа вкуса.
        Что передаём: избранное с сохранёнными жанрами и избранное без них.
        Что ожидаем: первые берутся из snapshot, вторые — из карточки каталога.
        """
        favorites = [
            Favorite(user_id=1, anime_id=10, genres=["Action"]),
            Favorite(user_id=1, anime_id=11, genres=None),
        ]
        anime_map = {
            11: Anime(external_id="11", title="Gintama", genres=["Comedy"]),
            12: None,
        }

        assert collect_genres(favorites, anime_map) == ["Action", "Comedy", "Comedy"]

    def test_build_top_anime_uses_weights_and_catalog_fields(self):
        """Что тестируем: карточки заметных тайтлов по весу внимания.
        Что передаём: пару «идентификатор, вес» и карточку каталога.
        Что ожидаем: название, обложка, рейтинг и округлённый вес на месте.
        """
        cards = build_top_anime(
            [(7, 12.345)],
            {7: Anime(external_id="7", title="Naruto", cover_url="cover-7", rating=8.4)},
        )

        assert cards[0].title == "Naruto"
        assert cards[0].cover_url == "cover-7"
        assert cards[0].rating == 8.4
        assert cards[0].weight == 12.3

    def test_card_builders_fall_back_to_identifier_without_catalog(self):
        """Что тестируем: поведение карточек, когда каталог молчит.
        Что передаём: пустой словарь карточек тайтлов.
        Что ожидаем: запасной заголовок по идентификатору и пустые обложки.
        """
        ratings = build_rating_cards(
            [UserAnimeRating(user_id=1, anime_id=7, score=4, rated_at=MOMENT)],
            {},
        )
        episodes = build_recent_episode_cards(
            [
                ViewingSession(
                    user_id=1,
                    anime_id=7,
                    episode=3,
                    watch_source_id=4,
                    position_seconds=10.0,
                    volume=1.0,
                    quality_label="720p",
                    is_paused=False,
                )
            ],
            {},
        )

        assert ratings[0].title == "Anime #7"
        assert ratings[0].cover_url is None
        assert ratings[0].rated_at == "2026-03-28 12:00"
        assert episodes[0].title == "Anime #7"
        assert episodes[0].original_title is None
        assert episodes[0].episode == 3

    def test_average_rating_ignores_titles_without_rating(self):
        """Что тестируем: среднюю оценку каталога по тайтлам профиля.
        Что передаём: карточку с оценкой, карточку без оценки и пропуск.
        Что ожидаем: среднее только по тайтлам с рейтингом.
        """
        mixed = average_catalog_rating(
            {
                1: Anime(external_id="1", title="A", rating=8.0),
                2: Anime(external_id="2", title="B", rating=None),
                3: None,
            }
        )
        empty = average_catalog_rating({1: None})

        assert mixed == 8.0
        assert empty is None

    def test_catalog_accessors_tolerate_missing_card(self):
        """Что тестируем: доступы к полям карточки при её отсутствии.
        Что передаём: None вместо карточки каталога.
        Что ожидаем: запасной заголовок, пустые обложка и оригинальное название.
        """
        assert title_of(None, 7) == "Anime #7"
        assert title_of(Anime(external_id="7", title="  "), 7) == "Anime #7"
        assert cover_of(None) is None
        assert original_title_of(None) is None
