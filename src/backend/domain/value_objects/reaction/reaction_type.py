"""Value objects: тип реакции на эпизод и её эмодзи."""

from enum import StrEnum


class EpisodeReactionType(StrEnum):
    """Типы реакций, которые пользователь ставит моменту серии."""

    FIRE = "fire"
    LOVE = "love"
    LAUGH = "laugh"
    CRY = "cry"
    SHOCK = "shock"
    SKULL = "skull"
    SPARKLE = "sparkle"

    @classmethod
    def from_value(cls, value: str | None) -> "EpisodeReactionType | None":
        """Определить тип реакции по сырой строке."""
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
