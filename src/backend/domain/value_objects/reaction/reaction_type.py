"""Value objects: тип реакции на эпизод и её эмодзи."""

from enum import StrEnum


class EpisodeReactionType(StrEnum):
    """Reaction types a user can attach to a specific episode moment."""

    FIRE = "fire"
    LOVE = "love"
    LAUGH = "laugh"
    CRY = "cry"
    SHOCK = "shock"
    SKULL = "skull"
    SPARKLE = "sparkle"

    @classmethod
    async def from_value(cls, value: str | None) -> "EpisodeReactionType | None":
        """Resolve a reaction type from a raw string.

        Args:
            value: Raw reaction label.

        Returns:
            EpisodeReactionType | None: The matching type or None when unknown.
        """
        if not value:
            return None
        try:
            return cls(str(value).strip().lower())
        except ValueError:
            return None

    @property
    def emoji(self) -> "EpisodeReactionEmoji":
        """Возвращает эмодзи-представление реакции для UI."""
        return EpisodeReactionEmoji[self.name]


class EpisodeReactionEmoji(StrEnum):
    """Эмодзи-представления типов реакций (value object для UI)."""

    FIRE = "🔥"
    LOVE = "❤️"
    LAUGH = "😂"
    CRY = "😭"
    SHOCK = "😱"
    SKULL = "💀"
    SPARKLE = "✨"

    @classmethod
    def for_type(cls, reaction_type: EpisodeReactionType) -> "EpisodeReactionEmoji":
        """Возвращает эмодзи по типу реакции."""
        return cls[reaction_type.name]
