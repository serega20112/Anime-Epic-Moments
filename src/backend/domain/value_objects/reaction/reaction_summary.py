"""Значимые объекты состояния реакций на серию."""

from __future__ import annotations

from dataclasses import dataclass, field

from backend.domain.value_objects.reaction.reaction_type import EpisodeReactionType


@dataclass(frozen=True, slots=True)
class EpisodeReactionCount:
    """Число реакций одного типа на серии."""

    reaction_type: EpisodeReactionType
    count: int


@dataclass(frozen=True, slots=True)
class EpisodeReactionSummary:
    """Сводка реакций серии и реакция самого зрителя."""

    counts: list[EpisodeReactionCount] = field(default_factory=list)
    user_reaction: EpisodeReactionType | None = None

    @classmethod
    def empty(cls) -> EpisodeReactionSummary:
        """Собрать сводку без реакций."""
        return cls(counts=[], user_reaction=None)
