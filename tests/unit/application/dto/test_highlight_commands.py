from __future__ import annotations

import pytest

from backend.application.dto.highlight import (
    AddHighlightCommentCommand,
    CreateHighlightCommand,
    DeleteHighlightCommand,
    EditHighlightCommand,
    HighlightDashboardQuery,
    HighlightFeedQuery,
    HighlightListQuery,
    SetHighlightLikeCommand,
    SetSavedHighlightCommand,
)


class TestCreateHighlightCommand:
    def test_stores_required_fields(self):
        command = CreateHighlightCommand(
            user_id=5,
            anime_id=1,
            episode=2,
            start_timestamp=10.0,
            end_timestamp=20.0,
        )
        assert command.user_id == 5
        assert command.anime_id == 1
        assert command.episode == 2
        assert command.start_timestamp == 10.0
        assert command.end_timestamp == 20.0

    def test_defaults(self):
        command = CreateHighlightCommand(
            user_id=None, anime_id=1, episode=1, start_timestamp=0, end_timestamp=5
        )
        assert command.title == ""
        assert command.category is None
        assert command.description == ""
        assert command.is_spoiler is False
        assert command.emotion is None
        assert command.highlights_this_hour == 0

    def test_is_frozen(self):
        command = CreateHighlightCommand(
            user_id=5, anime_id=1, episode=2, start_timestamp=0, end_timestamp=5
        )
        with pytest.raises(Exception):
            command.title = "x"


class TestEditHighlightCommand:
    def test_stores_fields(self):
        command = EditHighlightCommand(
            highlight_id=1,
            episode=2,
            start_timestamp=1.0,
            end_timestamp=2.0,
            title="t",
            category="c",
            description="d",
            is_spoiler=True,
            emotion="fun",
        )
        assert command.highlight_id == 1
        assert command.emotion == "fun"
        assert command.is_spoiler is True


class TestDeleteHighlightCommand:
    def test_stores_field(self):
        assert DeleteHighlightCommand(highlight_id=7).highlight_id == 7


class TestSetHighlightLikeCommand:
    def test_stores_fields(self):
        command = SetHighlightLikeCommand(highlight_id=1, user_id=2, liked=True)
        assert command.liked is True
        assert command.user_id == 2


class TestSetSavedHighlightCommand:
    def test_stores_fields(self):
        command = SetSavedHighlightCommand(highlight_id=1, user_id=2, saved=False)
        assert command.saved is False


class TestAddHighlightCommentCommand:
    def test_stores_fields(self):
        command = AddHighlightCommentCommand(highlight_id=1, user_id=2, content="nice")
        assert command.content == "nice"


class TestHighlightDashboardQuery:
    def test_defaults(self):
        query = HighlightDashboardQuery()
        assert query.anime_id is None
        assert query.emotion is None
        assert query.category is None
        assert query.sort_by == "recent"
        assert query.created_date is None
        assert query.query is None
        assert query.include_spoilers is False
        assert query.limit == 20
        assert query.viewer_user_id is None

    def test_stores_overrides(self):
        query = HighlightDashboardQuery(sort_by="popular", limit=5, include_spoilers=True)
        assert query.sort_by == "popular"
        assert query.limit == 5
        assert query.include_spoilers is True


class TestHighlightListQuery:
    def test_defaults(self):
        query = HighlightListQuery()
        assert query.include_spoilers is True
        assert query.sort_by == "recent"


class TestHighlightFeedQuery:
    def test_defaults(self):
        query = HighlightFeedQuery()
        assert query.include_spoilers is False
        assert query.limit == 12
        assert query.viewer_user_id is None
