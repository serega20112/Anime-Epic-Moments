"""Правила статусов просмотра, приоритета озвучек и ранжирования источников."""

import re

ANIME_STATUS_VALUES: tuple[str, ...] = (
    "watching",
    "completed",
    "paused",
    "dropped",
    "plan_to_watch",
)


def normalize_anime_status(value: str | None) -> str | None:
    """Нормализует статус дневника просмотра в канонический вид."""
    normalized = str(value or "").strip().lower().replace(" ", "_")
    if normalized not in ANIME_STATUS_VALUES:
        return None
    return normalized


def is_valid_anime_status(value: str | None) -> bool:
    """Проверяет, является ли значение допустимым статусом дневника."""
    return normalize_anime_status(value) is not None


PREFERRED_TRANSLATION_GROUPS: list[tuple[str, tuple[str, ...]]] = [
    (
        "StudioBand",
        (
            "студийная банда",
            "studioband",
            "studio band",
            "studio-band",
            "studio_band",
        ),
    ),
    ("AniDUB", ("анидуб", "ani dub", "ani-dub", "anidub", "anidub tv", "anidub.tv")),
    (
        "Komnata Didi",
        (
            "комната дидди",
            "комната диди",
            "komnata didi",
            "komnata-didi",
            "komnata_didi",
            "didi studio",
            "didi",
            "диди",
        ),
    ),
    (
        "Amazing Dubbing",
        (
            "эмэйзинг даббинг",
            "эмейзинг даббинг",
            "amazing dubbing",
            "amazing-dubbing",
            "amazing dub",
        ),
    ),
    ("AnimeVost", ("анимевост", "animevost", "anime vost", "anime-vost", "anvost")),
    ("AniLibria", ("анилибрия", "anilibria", "aniliberty")),
    (
        "SovetRomantica",
        (
            "советская романтика",
            "совромантика",
            "сов. романтика",
            "sovetromantica",
            "soviet romantica",
        ),
    ),
    ("Dream Cast", ("dream cast", "дрим каст", "дримкаст")),
    ("Daddy Cast", ("daddy cast", "дадди каст")),
    (
        "Kansai Studio",
        ("канзай", "kansai", "kansai studio", "кансай студио"),
    ),
    ("JAM", ("jam", "студия джем", "джем студио")),
    ("AniStar", ("anistar", "анистар", "ani star")),
    ("AniMaunt", ("animaunt", "анимаунт", "анимаут")),
    ("Shiza Project", ("shiza project", "шиза проект", "shiza")),
    ("Onibaku", ("onibaku", "онибаку")),
    ("Voice of Love", ("voice of love", "войс оф лав")),
    ("AniFlex", ("aniflex", "анифлекс")),
    ("Studio OD", ("studio od", "od studio", "студия од")),
    ("Heroic Voice", ("heroic voice", "хероик войс")),
    ("Kanobu", ("kanobu", "канабу")),
    ("AniRise", ("anirise", "анирайз", "ani rise")),
    ("Reanimedia", ("reanimedia", "реанимедиа")),
    ("String Studio", ("string studio", "стринг студио")),
    ("Sadim Sakura", ("sadim sakura", "садим сакура", "sadim-sakura")),
]


def normalize_translation_name(value: str | None) -> str:
    """Нормализует имя озвучки для сопоставления и ранжирования."""
    text = str(value or "").lower().strip()
    text = re.sub(r"[^a-zа-я0-9]+", " ", text, flags=re.IGNORECASE)
    return " ".join(text.split())


def get_translation_priority(value: str | None) -> tuple[int, str]:
    """Возвращает приоритет озвучки: чем меньше число, тем выше в выдаче."""
    normalized = normalize_translation_name(value)
    for index, (_label, aliases) in enumerate(PREFERRED_TRANSLATION_GROUPS):
        if any(alias in normalized for alias in aliases):
            return index, normalized
    return len(PREFERRED_TRANSLATION_GROUPS), normalized


def is_preferred_translation(value: str | None) -> bool:
    """Проверяет, входит ли озвучка в список предпочитаемых групп."""
    return (get_translation_priority(value))[0] < len(PREFERRED_TRANSLATION_GROUPS)


def canonicalize_translation_name(value: str | None) -> str:
    """Возвращает каноническое название группы озвучки для UI/сортировки."""
    normalized = normalize_translation_name(value)
    for label, aliases in PREFERRED_TRANSLATION_GROUPS:
        if any(alias in normalized for alias in aliases):
            return label
    return str(value or "").strip() or "Unknown"


SOURCE_TYPE_PRIORITIES: dict[str, int] = {
    "stream": 0,
    "embed": 1,
    "external": 2,
}
UNKNOWN_SOURCE_TYPE_PRIORITY = 3


def quality_rank(value: str | None) -> int:
    """Преобразует метку качества в числовой ранг для сортировки по убыванию.

    Args:
        value: Метка качества (``720p``, ``auto``).

    Returns:
        int: Числовой ранг; 0, если цифр в метке нет.
    """
    digits = "".join(character for character in str(value or "") if character.isdigit())
    return int(digits) if digits else 0


def source_type_priority(value: str | None) -> int:
    """Возвращает приоритет типа источника для выбора варианта по умолчанию.

    Args:
        value: Тип источника (``stream``, ``embed``, ``external``).

    Returns:
        int: Чем меньше число, тем выше приоритет.
    """
    normalized = str(value or "").strip().lower()
    return SOURCE_TYPE_PRIORITIES.get(normalized, UNKNOWN_SOURCE_TYPE_PRIORITY)


EPISODE_WATCHED_THRESHOLD = 0.9


def is_episode_watched(position_seconds: float | None, duration_seconds: float | None) -> bool:
    """Проверяет, достигнута ли пороговая доля просмотра серии.

    Порог «просмотрено» решает сервер: клиент сообщает только позицию и
    длительность. Без известной длительности серия не считается просмотренной,
    иначе ноль в длительности превращал бы любую позицию в завершённый просмотр.

    Args:
        position_seconds: Сохранённая позиция воспроизведения.
        duration_seconds: Длительность серии либо None, если она неизвестна.

    Returns:
        bool: True, когда позиция покрывает не меньше 90 % серии.
    """
    if not duration_seconds or duration_seconds <= 0:
        return False
    return max(0.0, float(position_seconds or 0.0)) >= duration_seconds * EPISODE_WATCHED_THRESHOLD
