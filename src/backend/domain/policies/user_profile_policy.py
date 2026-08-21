from __future__ import annotations

from collections import Counter

from backend.domain.value_objects.highlight.profile_summary import HighlightProfileSummary
from backend.domain.value_objects.user.smart_profile import (
    AchievementBadge,
    GenreAffinity,
    ProfileMoodInsight,
)


async def build_genre_affinities(genres: list[str], limit: int = 5) -> list[GenreAffinity]:
    """Возвращает топ жанров пользователя по частоте."""
    counter = Counter(str(genre).strip() for genre in genres if str(genre).strip())
    return [
        GenreAffinity(name=name, count=count)
        for name, count in counter.most_common(max(int(limit), 1))
    ]


async def detect_profile_mood(
    genres: list[str],
    emotions: list[str],
) -> ProfileMoodInsight:
    """Определяет доминирующий вайб пользователя по жанрам и эмоциям."""
    normalized_genres = {str(value).strip().lower() for value in genres if str(value).strip()}
    normalized_emotions = {str(value).strip().lower() for value in emotions if str(value).strip()}

    dark_markers = {
        "drama",
        "psychological",
        "thriller",
        "horror",
        "mystery",
        "tragedy",
        "supernatural",
    }
    action_markers = {
        "action",
        "adventure",
        "martial arts",
        "sports",
        "cars",
        "shounen",
        "military",
    }
    cozy_markers = {
        "comedy",
        "slice of life",
        "romance",
        "school",
        "music",
        "iyashikei",
    }
    fantasy_markers = {
        "fantasy",
        "magic",
        "isekai",
        "sci-fi",
    }

    if normalized_genres & dark_markers or normalized_emotions & {"sad", "tense", "dark"}:
        return ProfileMoodInsight(
            label="Тёмный вайб",
            description="Ты явно тянешься к драме, напряжению и тяжёлым эмоциям.",
            emoji="😈",
        )
    if normalized_genres & action_markers or normalized_emotions & {"hype", "epic", "adrenaline"}:
        return ProfileMoodInsight(
            label="Боевой драйв",
            description="Тебя цепляет скорость, экшен и моменты, где всё летит вразнос.",
            emoji="🔥",
        )
    if normalized_genres & cozy_markers or normalized_emotions & {"funny", "warm", "cute"}:
        return ProfileMoodInsight(
            label="Уютный режим",
            description="Ты любишь лёгкие, тёплые и расслабляющие тайтлы.",
            emoji="✨",
        )
    if normalized_genres & fantasy_markers:
        return ProfileMoodInsight(
            label="Приключенческий радар",
            description="Тебя стабильно уводит в новые миры, магию и путешествия.",
            emoji="🗺️",
        )
    return ProfileMoodInsight(
        label="Смешанный вкус",
        description="У тебя широкий профиль без одного доминирующего настроения.",
        emoji="🎭",
    )


async def build_achievement_badges(
    profile_summary: HighlightProfileSummary,
    hours_watched: float,
    favorite_genres: list[GenreAffinity],
    highlight_likes_received: int,
    top_mood: ProfileMoodInsight,
) -> list[AchievementBadge]:
    """Возвращает набор ачивок по статистике и вкусу пользователя."""
    badges: list[AchievementBadge] = []

    if hours_watched >= 10:
        badges.append(
            AchievementBadge(
                code="binge_watcher",
                title="Биндж-марафонец",
                description="Набрал двузначное число часов просмотра и явно не умеешь останавливаться на одной серии.",
                icon="⏱️",
                rarity="rare",
            )
        )
    if profile_summary.highlight_count >= 5:
        badges.append(
            AchievementBadge(
                code="moment_hunter",
                title="Охотник за моментами",
                description="Регулярно вырезаешь лучшие сцены и превращаешь просмотр в контент.",
                icon="🎬",
                rarity="epic",
            )
        )
    if profile_summary.saved_count >= 5:
        badges.append(
            AchievementBadge(
                code="collector",
                title="Коллекционер вайба",
                description="Собираешь моменты не импульсивно, а впрок, как нормальный куратор.",
                icon="📚",
                rarity="rare",
            )
        )
    if highlight_likes_received >= 10:
        badges.append(
            AchievementBadge(
                code="crowd_favorite",
                title="Любимец фида",
                description="Твои хайлайты уже стабильно собирают отклик у других зрителей.",
                icon="💥",
                rarity="legendary",
            )
        )
    if favorite_genres:
        top_genre = favorite_genres[0]
        if top_genre.count >= 3:
            badges.append(
                AchievementBadge(
                    code=f"genre_{top_genre.name.lower().replace(' ', '_')}",
                    title=f"Фанат жанра: {top_genre.name}",
                    description=f"Жанр {top_genre.name} встречается у тебя чаще всего и уже стал частью вкусового профиля.",
                    icon="🎯",
                    rarity="common",
                )
            )
    if top_mood.label == "Тёмный вайб":
        badges.append(
            AchievementBadge(
                code="dark_soul",
                title="Тёмная душа",
                description="Судя по выбору, тебя не интересуют безопасные истории без напряжения.",
                icon="🌒",
                rarity="rare",
            )
        )

    if not badges:
        badges.append(
            AchievementBadge(
                code="first_steps",
                title="Первый сезон",
                description="Профиль уже начал собирать вкус. Ещё немного активности и откроются более жирные ачивки.",
                icon="🌱",
                rarity="common",
            )
        )
    return badges[:6]
