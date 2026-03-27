import re
from src.backend.domain.anime.entity import Anime


class AnimeSafetyPolicy:
    """Доменная политика безопасного поиска аниме."""

    _ADULT_INTENT_MARKERS = (
        "hentai",
        "ecchi",
        "18+",
        "nsfw",
        "porn",
        "порно",
        "хентай",
        "эрот",
        "голые",
        "sex",
        "sexual",
    )
    _NSFW_CONTENT_MARKERS = (
        "hentai",
        "ecchi",
        "explicit",
        "porn",
        "эрот",
        "порно",
        "sexual",
        "sex",
    )

    @staticmethod
    def has_explicit_adult_intent(
        description: str, genre_hint: str | None = None
    ) -> bool:
        """Возвращает True, если пользователь явно ищет 18+ контент."""
        haystack = f"{description or ''} {genre_hint or ''}".lower()
        return any(
            marker in haystack for marker in AnimeSafetyPolicy._ADULT_INTENT_MARKERS
        )

    @staticmethod
    def is_probably_nsfw(anime: Anime) -> bool:
        """Возвращает True, если карточка аниме выглядит как NSFW-контент."""
        genres = " ".join(anime.genres or []).lower()
        text = f"{anime.title or ''} {anime.description or ''}".lower()
        haystack = f"{genres} {text}"
        return any(
            marker in haystack for marker in AnimeSafetyPolicy._NSFW_CONTENT_MARKERS
        )

    @staticmethod
    def suggest_title_hints(
        description: str, genre_hint: str | None = None
    ) -> list[str]:
        """Извлекает явные подсказки названий из пользовательского текста."""
        text = f"{description or ''} {genre_hint or ''}"
        raw_hints = re.findall(r"[\"'«](.+?)[\"'»]", text)
        hints: list[str] = []
        seen: set[str] = set()
        for raw_hint in raw_hints:
            normalized = " ".join(raw_hint.split()).strip()
            if not normalized or len(normalized) > 80:
                continue
            key = normalized.lower()
            if key in seen:
                continue
            seen.add(key)
            hints.append(normalized)
        return hints
