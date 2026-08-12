from __future__ import annotations

import pytest

from backend.application.dto.watch_commands import (
    AddAnimeCommentCommand,
    CreateWatchHighlightCommand,
    SaveViewingSessionCommand,
    SetAnimeCommentLikeCommand,
    UpsertUserAnimeStatusCommand,
    WatchPageQuery,
)


class TestUpsertUserAnimeStatusCommand:
    def test_stores_fields(self):
        command = UpsertUserAnimeStatusCommand(user_id=1, anime_id=2, status="planned")
        assert command.user_id == 1
        assert command.anime_id == 2
        assert command.status == "planned"

    def test_is_frozen(self):
        command = UpsertUserAnimeStatusCommand(user_id=1, anime_id=2, status="planned")
        with pytest.raises(Exception):
            command.status = "x"


class TestSaveViewingSessionCommand:
    def test_stores_fields(self):
        command = SaveViewingSessionCommand(
            user_id=1,
            anime_id=2,
            episode=3,
            watch_source_id=4,
            position_seconds=100.0,
            volume=0.5,
            quality_label="1080p",
            is_paused=True,
        )
        assert command.user_id == 1
        assert command.watch_source_id == 4
        assert command.position_seconds == 100.0
        assert command.volume == 0.5
        assert command.quality_label == "1080p"
        assert command.is_paused is True

    def test_defaults(self):
        command = SaveViewingSessionCommand(
            user_id=1, anime_id=2, episode=3, watch_source_id=4
        )
        assert command.position_seconds == 0.0
        assert command.volume == 1.0
        assert command.quality_label == "Auto"
        assert command.is_paused is False


class TestCreateWatchHighlightCommand:
    def test_stores_fields(self):
        command = CreateWatchHighlightCommand(
            user_id=1,
            anime_id=2,
            episode=3,
            title="epic",
            category="funny",
            start_timestamp=10.0,
            end_timestamp=20.0,
            description="d",
            is_spoiler=True,
            emotion="fun",
            watch_source_id=4,
            translation_id=5,
        )
        assert command.user_id == 1
        assert command.watch_source_id == 4
        assert command.translation_id == 5
        assert command.emotion == "fun"
        assert command.is_spoiler is True


class TestAddAnimeCommentCommand:
    def test_stores_fields(self):
        command = AddAnimeCommentCommand(anime_id=2, user_id=1, content="good")
        assert command.anime_id == 2
        assert command.content == "good"


class TestSetAnimeCommentLikeCommand:
    def test_stores_fields(self):
        command = SetAnimeCommentLikeCommand(comment_id=6, user_id=1, liked=True)
        assert command.comment_id == 6
        assert command.liked is True


class TestWatchPageQuery:
    def test_defaults(self):
        query = WatchPageQuery()
        assert query.episode == 1
        assert query.selected_source_id is None
        assert query.preferred_start_seconds is None
        assert query.discussion_sort == "popular"

    def test_stores_overrides(self):
        query = WatchPageQuery(
            episode=3,
            selected_source_id=4,
            preferred_start_seconds=50.0,
            discussion_sort="recent",
        )
        assert query.episode == 3
        assert query.selected_source_id == 4
        assert query.preferred_start_seconds == 50.0
        assert query.discussion_sort == "recent"