"""Value objects describing episode reaction state."""

from __future__ import annotations

from dataclasses import dataclass, field

from backend.domain.value_objects.reaction.reaction_type import EpisodeReactionType


@dataclass(frozen=True, slots=True)
class EpisodeReactionCount:
    """Number of reactions of a single type on an episode."""

    reaction_type: EpisodeReactionType
    count: int


@dataclass(frozen=True, slots=True)
class EpisodeReactionSummary:
    """Aggregated reaction state for an episode and viewer."""

    counts: list[EpisodeReactionCount] = field(default_factory=list)
    user_reaction: EpisodeReactionType | None = None

    @classmethod
    def empty(cls) -> EpisodeReactionSummary:
        """Build a summary with no reactions.

        Returns:
            EpisodeReactionSummary: Empty summary.
        """
        return cls(counts=[], user_reaction=None)
