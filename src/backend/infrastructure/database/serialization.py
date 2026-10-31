"""Общие преобразования колонок базы в доменные значения.

Сериализация списков жанров нужна и избранному, и коллекциям: колонка одна и
та же (`genres_json`), поэтому и разбор должен быть один — иначе при изменении
формата одна из таблиц тихо начала бы отдавать пустые жанры.
"""

from __future__ import annotations

import json
from collections.abc import Iterable


def dump_genres(genres: Iterable[str] | None) -> str | None:
    """Сериализовать жанры в JSON-колонку.

    Args:
        genres: Жанры тайтла либо None.

    Returns:
        str | None: JSON-строка для базы либо None, если значимых жанров нет.
    """
    cleaned = [str(genre).strip() for genre in genres or [] if str(genre).strip()]
    return json.dumps(cleaned, ensure_ascii=False) if cleaned else None


def load_genres(payload: str | None) -> list[str]:
    """Разобрать JSON-колонку жанров, устойчиво к мусору в базе.

    Args:
        payload: Значение колонки `genres_json`.

    Returns:
        list[str]: Жанры без пустых значений; пустой список при ошибке разбора.
    """
    if not payload:
        return []
    try:
        data = json.loads(payload)
    except (TypeError, ValueError):
        return []
    if not isinstance(data, list):
        return []
    return [str(item).strip() for item in data if str(item).strip()]
