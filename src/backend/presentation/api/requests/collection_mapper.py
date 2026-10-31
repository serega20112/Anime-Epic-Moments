"""Сборка команд application из HTTP-форм коллекций."""

from __future__ import annotations

from backend.application.dto import CreateCollectionCommand, RemoveCollectionItemCommand

TITLE_MAX_LENGTH = 80
DESCRIPTION_MAX_LENGTH = 400


def map_create_collection_command(form, *, user_id: int) -> CreateCollectionCommand:
    """Собрать команду создания коллекции из формы.

    Args:
        form: Разобранная форма Starlette.
        user_id: Идентификатор владельца коллекции.

    Returns:
        CreateCollectionCommand: Команда создания коллекции.
    """
    return CreateCollectionCommand(
        user_id=user_id,
        title=_trim(form.get("title"), TITLE_MAX_LENGTH),
        description=_trim(form.get("description"), DESCRIPTION_MAX_LENGTH),
        is_public=_to_bool(form.get("is_public"), default=True),
        cover_url=_optional(form.get("cover_url")),
    )


def map_remove_collection_item_command(
    form, *, collection_id: int, user_id: int
) -> RemoveCollectionItemCommand:
    """Собрать команду удаления аниме из коллекции из формы.

    Args:
        form: Разобранная форма Starlette.
        collection_id: Идентификатор коллекции из пути.
        user_id: Идентификатор действующего пользователя.

    Returns:
        RemoveCollectionItemCommand: Команда удаления элемента коллекции.
    """
    return RemoveCollectionItemCommand(
        collection_id=collection_id,
        anime_id=_to_int(form.get("anime_id")) or 0,
        user_id=user_id,
    )


def _trim(value, max_length: int) -> str:
    """Обрезать значение до предельной длины.

    Args:
        value: Значение поля формы.
        max_length: Предельная длина строки.

    Returns:
        str: Обрезанная строка без пробелов по краям.
    """
    return str(value or "").strip()[:max_length]


def _optional(value) -> str | None:
    """Свести пустое необязательное значение к None.

    Args:
        value: Значение поля формы.

    Returns:
        str | None: Текст либо None для пустого значения.
    """
    text = str(value or "").strip()
    return text or None


def _to_bool(value, *, default: bool) -> bool:
    """Преобразовать значение формы в булево.

    Args:
        value: Значение поля формы.
        default: Значение для отсутствующего поля.

    Returns:
        bool: Разобранный признак.
    """
    if value in (None, ""):
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _to_int(value) -> int | None:
    """Преобразовать значение формы в целое число.

    Args:
        value: Значение поля формы.

    Returns:
        int | None: Число либо None, если значение не является целым.
    """
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
