from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from backend.application.dto import (
    GetEpisodeReactionsQuery,
    SetEpisodeReactionCommand,
)
from backend.application.use_cases import (
    GetEpisodeReactionsUseCase,
    SetEpisodeReactionUseCase,
)
from backend.domain import EpisodeReactionType
from backend.domain.reaction.value_object import EpisodeReactionCount


@pytest.mark.unit
class TestGetEpisodeReactionsUseCase:
    """Юнит-тесты чтения реакции на эпизод."""

    async def test_returns_counts_and_user_reaction(self):
        """Что тестируем: агрегацию счётчиков и реакции зрителя.
        Что передаём: замоканный репозиторий со счётчиками и реакцией.
        Что ожидаем: результат успешен, данные содержат счётчики и user_reaction.
        """
        reaction_repo = AsyncMock()
        reaction_repo.get_reaction_counts.return_value = [
            EpisodeReactionCount(reaction_type=EpisodeReactionType.FIRE, count=3)
        ]
        reaction_repo.get_user_reaction.return_value = SimpleReaction(EpisodeReactionType.FIRE)
        use_case = GetEpisodeReactionsUseCase(reaction_repo)

        result = await use_case.execute(
            GetEpisodeReactionsQuery(anime_id=9, episode=2, user_id=1)
        )

        assert result.ok is True
        assert result.data.counts[0].count == 3
        assert result.data.user_reaction == EpisodeReactionType.FIRE

    async def test_rejects_invalid_episode(self):
        """Что тестируем: отказ при невалидном номере эпизода.
        Что передаём: episode = 0.
        Что ожидаем: failure со статусом 400, репозиторий не вызывается.
        """
        reaction_repo = AsyncMock()
        use_case = GetEpisodeReactionsUseCase(reaction_repo)

        result = await use_case.execute(
            GetEpisodeReactionsQuery(anime_id=9, episode=0, user_id=1)
        )

        assert result.ok is False
        assert result.status_code == 400
        reaction_repo.get_reaction_counts.assert_not_awaited()


@pytest.mark.unit
class TestSetEpisodeReactionUseCase:
    """Юнит-тесты установки/удаления реакции на эпизод."""

    async def test_sets_reaction(self):
        """Что тестируем: создание реакции при liked=True.
        Что передаём: валидный тип реакции.
        Что ожидаем: set_reaction вызван с корректной сущностью, вернулся summary.
        """
        reaction_repo = AsyncMock()
        reaction_repo.get_reaction_counts.return_value = []
        reaction_repo.get_user_reaction.return_value = SimpleReaction(EpisodeReactionType.LOVE)
        use_case = SetEpisodeReactionUseCase(reaction_repo)

        result = await use_case.execute(
            SetEpisodeReactionCommand(
                user_id=1,
                anime_id=9,
                episode=2,
                reaction_type="love",
                timestamp=12.5,
                liked=True,
            )
        )

        assert result.ok is True
        assert result.data.user_reaction == EpisodeReactionType.LOVE
        reaction = reaction_repo.set_reaction.await_args.args[0]
        assert reaction.user_id == 1
        assert reaction.anime_id == 9
        assert reaction.episode == 2
        assert reaction.timestamp == 12.5

    async def test_removes_reaction(self):
        """Что тестируем: удаление реакции при liked=False.
        Что передаём: liked=False.
        Что ожидаем: remove_reaction вызван, set_reaction не вызван.
        """
        reaction_repo = AsyncMock()
        reaction_repo.get_reaction_counts.return_value = []
        reaction_repo.get_user_reaction.return_value = None
        use_case = SetEpisodeReactionUseCase(reaction_repo)

        result = await use_case.execute(
            SetEpisodeReactionCommand(
                user_id=1,
                anime_id=9,
                episode=2,
                reaction_type="love",
                liked=False,
            )
        )

        assert result.ok is True
        assert result.data.user_reaction is None
        reaction_repo.remove_reaction.assert_awaited_once_with(1, 9, 2)
        reaction_repo.set_reaction.assert_not_awaited()

    async def test_rejects_unknown_reaction_type(self):
        """Что тестируем: отказ при неизвестном типе реакции.
        Что передаём: reaction_type="alien".
        Что ожидаем: failure со статусом 400, репозиторий не вызывается.
        """
        reaction_repo = AsyncMock()
        use_case = SetEpisodeReactionUseCase(reaction_repo)

        result = await use_case.execute(
            SetEpisodeReactionCommand(
                user_id=1,
                anime_id=9,
                episode=2,
                reaction_type="alien",
                liked=True,
            )
        )

        assert result.ok is False
        assert result.status_code == 400
        reaction_repo.set_reaction.assert_not_awaited()


class SimpleReaction:
    """Минимальный заменитель EpisodeReaction для тестов."""

    def __init__(self, reaction_type):
        self.reaction_type = reaction_type

