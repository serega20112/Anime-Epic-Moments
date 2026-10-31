"""Кодек кэша: JSON с явными метками типов.

В кэше лежат доменные dataclass'ы, но формат хранения — обычный JSON без
pickle: небезопасную десериализацию в разделяемом хранилище использовать
нельзя. Поэтому dataclass и datetime помечаются служебными ключами, а при
чтении восстанавливаются по полному имени класса.
"""

from __future__ import annotations

import dataclasses
import datetime
import importlib
import json
from collections.abc import Mapping
from typing import Any

DATACLASS_MARKER = "__dataclass__"
DATETIME_MARKER = "__datetime__"
FIELDS_MARKER = "__fields__"


def encode(value: Any) -> Any:
    """Приводит значение к JSON-совместимому виду с метками типов.

    Args:
        value: Произвольное значение из домена.

    Returns:
        Any: Значение, которое умеет принять ``json.dumps``.

    Raises:
        TypeError: Тип значения не поддерживается кэшем.
    """
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return {
            DATACLASS_MARKER: f"{value.__class__.__module__}.{value.__class__.__qualname__}",
            FIELDS_MARKER: {
                field.name: encode(getattr(value, field.name))
                for field in dataclasses.fields(value)
            },
        }
    if isinstance(value, datetime.datetime):
        return {DATETIME_MARKER: value.isoformat()}
    if isinstance(value, (tuple, set, frozenset, list)):
        return [encode(item) for item in value]
    if isinstance(value, Mapping):
        return {str(key): encode(item) for key, item in value.items()}
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise TypeError(f"cannot serialize value of type {type(value).__name__}")


def resolve_class(qualified_name: str) -> type:
    """Находит класс по строке ``модуль.КвалифицированноеИмя``.

    Args:
        qualified_name: Полное имя класса.

    Returns:
        type: Найденный класс.

    Raises:
        TypeError: Имя указывает не на класс.
        ValueError: Имя не содержит имени модуля.
    """
    module_name, _, class_name = qualified_name.rpartition(".")
    if not module_name:
        raise ValueError(f"{qualified_name} does not name a module")
    module = importlib.import_module(module_name)
    for part in class_name.split("."):
        module = getattr(module, part)
    if not isinstance(module, type):
        raise TypeError(f"{qualified_name} does not name a class")
    return module


def decode(value: Any) -> Any:
    """Восстанавливает dataclass'ы и datetime из разобранного JSON.

    Args:
        value: Значение после ``json.loads``.

    Returns:
        Any: Значение с восстановленными типами.
    """
    if isinstance(value, dict):
        if DATETIME_MARKER in value:
            return datetime.datetime.fromisoformat(value[DATETIME_MARKER])
        if DATACLASS_MARKER in value:
            cls = resolve_class(value[DATACLASS_MARKER])
            fields = {key: decode(item) for key, item in value[FIELDS_MARKER].items()}
            return cls(**fields)
        return {key: decode(item) for key, item in value.items()}
    if isinstance(value, list):
        return [decode(item) for item in value]
    return value


def serialize(value: Any) -> str:
    """Сериализует значение в JSON-строку с метками типов.

    Args:
        value: Сохраняемое значение.

    Returns:
        str: JSON-строка без лишних пробелов.

    Raises:
        TypeError: Значение содержит неподдерживаемый кэшем тип.
    """
    return json.dumps(encode(value), ensure_ascii=False, separators=(",", ":"))


def deserialize(raw_value: str, default: Any) -> Any:
    """Разбирает JSON-строку и возвращает значение по умолчанию при порче.

    Args:
        raw_value: JSON-строка из хранилища.
        default: Значение на случай повреждённой записи.

    Returns:
        Any: Восстановленное значение или ``default``.
    """
    try:
        return decode(json.loads(raw_value))
    except (ValueError, TypeError, KeyError, AttributeError, ImportError, OSError):
        return default
