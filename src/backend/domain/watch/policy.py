import re

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
    return get_translation_priority(value)[0] < len(PREFERRED_TRANSLATION_GROUPS)


def canonicalize_translation_name(value: str | None) -> str:
    """Возвращает каноническое название группы озвучки для UI/сортировки."""
    normalized = normalize_translation_name(value)
    for label, aliases in PREFERRED_TRANSLATION_GROUPS:
        if any(alias in normalized for alias in aliases):
            return label
    return str(value or "").strip() or "Unknown"
