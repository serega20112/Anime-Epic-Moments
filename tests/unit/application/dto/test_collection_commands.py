from __future__ import annotations

import pytest

from backend.application.dto.collection_commands import (
    AddCollectionItemCommand,
    CreateCollectionCommand,
    RemoveCollectionItemCommand,
)


class TestCreateCollectionCommand:
    def test_stores_fields(self):
        command = CreateCollectionCommand(
            user_id=1,
            title="Favorites",
            description="My picks",
            is_public=False,
        )
        assert command.user_id == 1
        assert command.title == "Favorites"
        assert command.description == "My picks"
        assert command.is_public is False

    def test_defaults(self):
        command = CreateCollectionCommand(user_id=1, title="List")
        assert command.description == ""
        assert command.is_public is True

    def test_is_frozen(self):
        command = CreateCollectionCommand(user_id=1, title="List")
        with pytest.raises(Exception):
            command.title = "X"


class TestAddCollectionItemCommand:
    def test_stores_fields(self):
        command = AddCollectionItemCommand(
            collection_id=2,
            anime_id=9,
            title="A",
            description="d",
            cover_url="c.png",
            genres=["Action"],
        )
        assert command.collection_id == 2
        assert command.anime_id == 9
        assert command.cover_url == "c.png"
        assert command.genres == ["Action"]

    def test_defaults(self):
        command = AddCollectionItemCommand(collection_id=2, anime_id=9, title="A")
        assert command.description == ""
        assert command.cover_url is None
        assert command.genres == []

    def test_genres_are_not_shared(self):
        first = AddCollectionItemCommand(collection_id=2, anime_id=9, title="A")
        second = AddCollectionItemCommand(collection_id=2, anime_id=9, title="A")
        assert first.genres is not second.genres


class TestRemoveCollectionItemCommand:
    def test_stores_fields(self):
        command = RemoveCollectionItemCommand(collection_id=2, anime_id=9)
        assert command.collection_id == 2
        assert command.anime_id == 9