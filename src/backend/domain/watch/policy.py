import re

ANIME_STATUS_VALUES: tuple[str, ...] = (
    "watching",
    "completed",
    "paused",
    "dropped",
    "plan_to_watch",
)


async def normalize_anime_status(value: str | None) -> str | None:
    """Нормализует статус дневника просмотра в канонический вид."""
    normalized = str(value or "").strip().lower().replace(" ", "_")
    if normalized not in ANIME_STATUS_VALUES:
        return None
    return normalized


async def is_valid_anime_status(value: str | None) -> bool:
    """Проверяет, является ли значение допустимым статусом дневника."""
    return await normalize_anime_status(value) is not None

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


async def normalize_translation_name(value: str | None) -> str:
    """Нормализует имя озвучки для сопоставления и ранжирования."""
    text = str(value or "").lower().strip()
    text = re.sub(r"[^a-zа-я0-9]+", " ", text, flags=re.IGNORECASE)
    return " ".join(text.split())


async def get_translation_priority(value: str | None) -> tuple[int, str]:
    """Возвращает приоритет озвучки: чем меньше число, тем выше в выдаче."""
    normalized = await normalize_translation_name(value)
    for index, (_label, aliases) in enumerate(PREFERRED_TRANSLATION_GROUPS):
        if any(alias in normalized for alias in aliases):
            return index, normalized
    return len(PREFERRED_TRANSLATION_GROUPS), normalized


async def is_preferred_translation(value: str | None) -> bool:
    """Проверяет, входит ли озвучка в список предпочитаемых групп."""
    return (await get_translation_priority(value))[0] < len(PREFERRED_TRANSLATION_GROUPS)


async def canonicalize_translation_name(value: str | None) -> str:
    """Возвращает каноническое название группы озвучки для UI/сортировки."""
    normalized = await normalize_translation_name(value)
    for label, aliases in PREFERRED_TRANSLATION_GROUPS:
        if any(alias in normalized for alias in aliases):
            return label
    return str(value or "").strip() or "Unknown"
