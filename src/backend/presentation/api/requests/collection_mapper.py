"""Build application-layer command DTOs from collection HTTP forms.

All form parsing, normalization and validation live here so that route
handlers stay thin and only orchestrate use case execution.
"""

from __future__ import annotations

from backend.application.dto import (
    AddCollectionItemCommand,
    CreateCollectionCommand,
    RemoveCollectionItemCommand,
)

TITLE_MAX_LENGTH = 80
DESCRIPTION_MAX_LENGTH = 400
ITEM_TITLE_MAX_LENGTH = 120


def map_create_collection_command(form, *, user_id: int) -> CreateCollectionCommand:
    """Build a create collection command from form data.

    Args:
        form: Parsed form data.
        user_id: Owner user identifier.

    Returns:
        CreateCollectionCommand: Validated create command.
    """
    return CreateCollectionCommand(
        user_id=user_id,
        title=_trim(form.get("title"), TITLE_MAX_LENGTH),
        description=_trim(form.get("description"), DESCRIPTION_MAX_LENGTH),
        is_public=_to_bool(form.get("is_public"), default=True),
    )


def map_add_collection_item_command(form, *, collection_id: int) -> AddCollectionItemCommand:
    """Build an add collection item command from form data.

    Args:
        form: Parsed form data.
        collection_id: Target collection identifier.

    Returns:
        AddCollectionItemCommand: Validated add item command.
    """
    return AddCollectionItemCommand(
        collection_id=collection_id,
        anime_id=_to_int(form.get("anime_id")) or 0,
        title=_trim(form.get("title"), ITEM_TITLE_MAX_LENGTH),
        description=_trim(form.get("description"), DESCRIPTION_MAX_LENGTH),
        cover_url=_optional(form.get("cover_url")),
        genres=_genres(form),
    )


def map_remove_collection_item_command(form, *, collection_id: int) -> RemoveCollectionItemCommand:
    """Build a remove collection item command from form data.

    Args:
        form: Parsed form data.
        collection_id: Target collection identifier.

    Returns:
        RemoveCollectionItemCommand: Validated remove item command.
    """
    return RemoveCollectionItemCommand(
        collection_id=collection_id,
        anime_id=_to_int(form.get("anime_id")) or 0,
    )


def _trim(value, max_length: int) -> str:
    """Trim a value to a maximum length.

    Args:
        value: Raw value.
        max_length: Maximum allowed length.

    Returns:
        str: Stripped and truncated text.
    """
    return str(value or "").strip()[:max_length]


def _optional(value) -> str | None:
    """Normalize an optional text value.

    Args:
        value: Raw value.

    Returns:
        str | None: Stripped text or None if empty.
    """
    text = str(value or "").strip()
    return text or None


def _to_bool(value, *, default: bool) -> bool:
    """Convert a form value to a boolean.

    Args:
        value: Raw value.
        default: Value used when the input is missing.

    Returns:
        bool: Parsed boolean.
    """
    if value in (None, ""):
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _to_int(value) -> int | None:
    """Convert a form value to an integer.

    Args:
        value: Raw value.

    Returns:
        int | None: Parsed integer or None if invalid.
    """
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _genres(form) -> list[str]:
    """Extract and normalize a genres list from form data.

    Handles both repeated ``genres`` fields and a single comma-separated string.

    Args:
        form: Parsed form data.

    Returns:
        list[str]: Normalized genres.
    """
    values = form.getlist("genres") if hasattr(form, "getlist") else form.get("genres")
    if isinstance(values, str):
        values = [values]
    genres: list[str] = []
    for value in values or []:
        if value and "," in str(value):
            genres.extend(part.strip() for part in str(value).split(",") if part.strip())
        elif value:
            genres.append(str(value).strip())
    return [item for item in genres if item]
