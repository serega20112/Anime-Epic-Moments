from __future__ import annotations

import pytest

from backend.application.dto.recommendation_commands import AskAiRecommendationsCommand


class TestAskAiRecommendationsCommand:
    def test_stores_fields(self):
        command = AskAiRecommendationsCommand(user_id=3, query="komedii", limit=8)
        assert command.user_id == 3
        assert command.query == "komedii"
        assert command.limit == 8

    def test_default_limit(self):
        command = AskAiRecommendationsCommand(user_id=3, query="boevik")
        assert command.limit == 6

    def test_is_frozen(self):
        command = AskAiRecommendationsCommand(user_id=3, query="boevik")
        with pytest.raises(Exception):
            command.query = "x"
