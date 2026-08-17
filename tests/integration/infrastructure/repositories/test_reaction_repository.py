from __future__ import annotations

import pytest

from backend.domain import EpisodeReaction, EpisodeReactionType, User
from backend.infrastructure.repositories.reaction_repository import ReactionRepository
from backend.infrastructure.repositories.user_repository import UserRepository


@pytest.mark.integration
class TestReactionRepository:
    """Интеграционные тесты ReactionRepository на in-memory базе."""

    async def test_sets_updates_and_reads_reaction(self, async_db_session):
        """Проверяем, что ReactionRepository создает и обновляет реакцию на эпизод."""
        user = await UserRepository(async_db_session).add(
            User(email="reaction@example.com", username="reactor", password_hash="hash")
        )
        repo = ReactionRepository(async_db_session)

        created = await repo.set_reaction(
            EpisodeReaction(
                user_id=user.id,
                anime_id=7,
                episode=3,
                reaction_type=EpisodeReactionType.FIRE,
                timestamp=12.5,
            )
        )
        updated = await repo.set_reaction(
            EpisodeReaction(
                user_id=user.id,
                anime_id=7,
                episode=3,
                reaction_type=EpisodeReactionType.LOVE,
                timestamp=20.0,
            )
        )
        loaded = await repo.get_user_reaction(user.id, 7, 3)

        assert created.id is not None
        assert updated.id == created.id
        assert loaded is not None
        assert loaded.reaction_type == EpisodeReactionType.LOVE
        assert loaded.timestamp == 20.0

    async def test_counts_and_removes_reaction(self, async_db_session):
        """Проверяем, что счётчики агрегируются и реакция удаляется."""
        user = await UserRepository(async_db_session).add(
            User(email="reaction-count@example.com", username="counter", password_hash="hash")
        )
        repo = ReactionRepository(async_db_session)
        await repo.set_reaction(
            EpisodeReaction(
                user_id=user.id,
                anime_id=7,
                episode=3,
                reaction_type=EpisodeReactionType.FIRE,
            )
        )

        counts = await repo.get_reaction_counts(7, 3)
        assert len(counts) == 1
        assert counts[0].reaction_type == EpisodeReactionType.FIRE
        assert counts[0].count == 1

        removed = await repo.remove_reaction(user.id, 7, 3)
        assert removed is True
        assert await repo.get_user_reaction(user.id, 7, 3) is None
        assert await repo.get_reaction_counts(7, 3) == []
