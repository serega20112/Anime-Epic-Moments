from __future__ import annotations

import pytest

from src.backend.infrastructure.models.sqlalchemy_models import (
    FavoriteModel,
    HighlightContextModel,
    HighlightModel,
    TranslationModel,
    UserAnimeStatusModel,
    UserModel,
    ViewingSessionModel,
    WatchSourceModel,
)


@pytest.mark.parametrize(
    ("model", "expected_columns"),
    [
        (UserModel, {"id", "email", "username", "password_hash", "avatar_url", "created_at"}),
        (
            HighlightModel,
            {
                "id",
                "user_id",
                "anime_id",
                "episode",
                "start_timestamp",
                "end_timestamp",
                "description",
                "is_spoiler",
                "created_at",
                "likes_count",
                "emotion",
            },
        ),
        (
            FavoriteModel,
            {
                "id",
                "user_id",
                "anime_id",
                "title",
                "description",
                "cover_url",
                "genres_json",
                "added_at",
            },
        ),
        (
            UserAnimeStatusModel,
            {"id", "user_id", "anime_id", "status", "updated_at"},
        ),
        (
            TranslationModel,
            {"id", "anime_id", "name", "translation_type", "language", "created_at"},
        ),
        (
            WatchSourceModel,
            {
                "id",
                "anime_id",
                "episode",
                "translation_id",
                "provider_name",
                "source_name",
                "stream_url",
                "quality_label",
                "source_type",
                "created_at",
            },
        ),
        (
            ViewingSessionModel,
            {
                "id",
                "user_id",
                "anime_id",
                "episode",
                "watch_source_id",
                "position_seconds",
                "volume",
                "quality_label",
                "is_paused",
                "updated_at",
            },
        ),
        (
            HighlightContextModel,
            {
                "id",
                "highlight_id",
                "watch_source_id",
                "translation_id",
                "title",
                "created_at",
            },
        ),
    ],
)
def test_sqlalchemy_models_expose_expected_columns(model, expected_columns):
    """Проверяем, что SQLAlchemy-модели содержат нужные столбцы для текущего backend-контракта."""
    assert set(model.__table__.columns.keys()) == expected_columns
