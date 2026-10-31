"""Чистые мапперы ответа Kodik API в доменные VO доступности серий.

Модуль не делает сетевых вызовов и не знает про HTTP-клиент: только разбор
структуры ``results[]`` ответа ``/search``. Каждый элемент ``results`` —
отдельная озвучка со своим диапазоном серий, поэтому счётчики изолируются
по ``translation.id`` и никогда не берутся из метаданных каталога.
"""

from __future__ import annotations

from backend.domain.value_objects.watch.translation_availability import (
    TranslationEpisodeAvailability,
)


def map_kodik_translations_to_episodes(payload: object) -> list[TranslationEpisodeAvailability]:
    """Строит карту доступности серий по озвучкам из ответа Kodik /search.

    Поддерживает две формы ответа: сериалы с ``seasons[season].episodes``
    (ключи-номера серий) и одиночные материалы/фильмы (``last_episode`` /
    ``episodes_count``). Счётчик серий берётся только из данных самой
    озвучки — глобальные поля верхнего уровня игнорируются.

    Args:
        payload: Разобранный JSON ответа Kodik (dict с ключом ``results``).

    Returns:
        list[TranslationEpisodeAvailability]: По одной записи на озвучку,
        с отсортированным списком доступных серий.
    """
    if not isinstance(payload, dict):
        return []
    results = payload.get("results")
    if not isinstance(results, list):
        return []

    availability: list[TranslationEpisodeAvailability] = []
    for material in results:
        if not isinstance(material, dict):
            continue
        record = _map_material(material)
        if record is not None:
            availability.append(record)
    return availability


def _map_material(material: dict) -> TranslationEpisodeAvailability | None:
    """Разбирает один элемент ``results[]`` в запись доступности.

    Args:
        material: Элемент массива ``results`` ответа Kodik.

    Returns:
        TranslationEpisodeAvailability | None: None для битых записей
        без валидного ``translation.id`` или без серий.
    """
    translation = material.get("translation") or {}
    try:
        translation_id = int(translation.get("id"))
    except (TypeError, ValueError):
        return None

    title = str(translation.get("title") or "").strip() or "Unknown"
    translation_type = _map_translation_type(str(translation.get("type") or "voice").strip())

    episodes = _collect_episode_numbers(material)
    if not episodes:
        return None

    return TranslationEpisodeAvailability(
        translation_id=translation_id,
        title=title,
        translation_type=translation_type,
        episodes_count=len(episodes),
        available_episodes=sorted(set(episodes)),
        link=str(material.get("link") or "").strip() or None,
    )


def _collect_episode_numbers(material: dict) -> list[int]:
    """Собирает номера серий одного материала.

    Приоритет: явная структура ``seasons -> episodes`` (ключи-номера серий),
    затем диапазон ``first_episode``/``last_episode``/``episodes_count`` для
    сериалов без seasons; одиночные материалы (фильмы) считаются серией 1.

    Args:
        material: Элемент массива ``results`` ответа Kodik.

    Returns:
        list[int]: Номера серий этой озвучки (может быть пустым).
    """
    seasons = material.get("seasons")
    if isinstance(seasons, dict) and seasons:
        collected = _collect_episode_numbers_from_seasons(seasons)
        if collected:
            return collected
    first = _as_int(material.get("first_episode")) or 1
    last = _as_int(material.get("last_episode"))
    count = _as_int(material.get("episodes_count"))
    upper = last or count
    if upper and upper >= first:
        return list(range(first, upper + 1))
    return [1]


def _collect_episode_numbers_from_seasons(seasons: dict) -> list[int]:
    """Собирает номера серий из всех сезонов структуры seasons.

    Args:
        seasons: Значение поля ``seasons`` материала Kodik.

    Returns:
        list[int]: Все номера серий всех сезонов.
    """
    numbers: list[int] = []
    for season in seasons.values():
        if not isinstance(season, dict):
            continue
        episodes = season.get("episodes") or {}
        if not isinstance(episodes, dict):
            continue
        for key in episodes:
            try:
                numbers.append(int(key))
            except (TypeError, ValueError):
                continue
    return numbers


def _map_translation_type(value: str) -> str:
    """Нормализует тип дорожки Kodik в доменное значение (voice/sub).

    Args:
        value: Сырое значение поля ``translation.type``.

    Returns:
        str: "sub" для сабов, иначе "voice".
    """
    lowered = str(value or "").strip().lower()
    if lowered == "subtitles":
        return "sub"
    return lowered or "voice"


def _as_int(value: object) -> int | None:
    """Безопасно приводит значение к int, не бросая исключений.

    Args:
        value: Произвольное значение из JSON.

    Returns:
        int | None: Число или None, если приведение невозможно.
    """
    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
