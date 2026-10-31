"""Сборка команд и запросов application из HTTP-запросов хайлайтов."""

from __future__ import annotations

from fastapi import Request

from backend.application.dto import (
    AddHighlightCommentCommand,
    CreateHighlightCommand,
    DeleteHighlightCommand,
    EditHighlightCommand,
    HighlightDashboardQuery,
    HighlightFeedQuery,
    SetHighlightLikeCommand,
    SetSavedHighlightCommand,
)
from backend.presentation.api.requests.highlight_requests import (
    TITLE_MAX_LENGTH,
    AddHighlightCommentRequest,
    CreateHighlightRequest,
    EditHighlightRequest,
)

DESCRIPTION_MAX_LENGTH = 600
CATEGORY_MAX_LENGTH = 60
EMOTION_MAX_LENGTH = 40
SORT_MAX_LENGTH = 20
DATE_MAX_LENGTH = 10
SEARCH_MAX_LENGTH = 200


def map_create_highlight_command(
    body: CreateHighlightRequest,
    *,
    user_id: int | None,
    highlights_this_hour: int,
) -> CreateHighlightCommand:
    """Собрать команду создания хайлайта из валидированного тела.

    Идентификатор автора и счётчик добавлений приходят с сервера: значения из
    тела запроса игнорируются, иначе клиент смог бы подделать автора и обойти
    гостевую квоту.

    Args:
        body: Разобранное и проверенное тело запроса.
        user_id: Идентификатор автора либо None для гостя.
        highlights_this_hour: Серверный счётчик добавлений за текущее окно.

    Returns:
        CreateHighlightCommand: Команда создания хайлайта.
    """
    return CreateHighlightCommand(
        user_id=user_id,
        anime_id=body.anime_id,
        episode=body.episode,
        start_timestamp=body.start_timestamp,
        end_timestamp=body.end_timestamp,
        title=_trim(body.title, TITLE_MAX_LENGTH),
        category=_optional(body.category, CATEGORY_MAX_LENGTH),
        description=_trim(body.description, DESCRIPTION_MAX_LENGTH),
        is_spoiler=body.is_spoiler,
        emotion=_optional(body.emotion, EMOTION_MAX_LENGTH),
        highlights_this_hour=highlights_this_hour,
    )


def map_edit_highlight_command(
    body: EditHighlightRequest,
    *,
    highlight_id: int,
    user_id: int,
) -> EditHighlightCommand:
    """Собрать команду правки хайлайта из валидированного тела.

    Args:
        body: Разобранное и проверенное тело запроса.
        highlight_id: Идентификатор хайлайта из пути.
        user_id: Идентификатор автора хайлайта.

    Returns:
        EditHighlightCommand: Команда редактирования хайлайта.
    """
    return EditHighlightCommand(
        highlight_id=highlight_id,
        user_id=user_id,
        episode=body.episode,
        start_timestamp=body.start_timestamp,
        end_timestamp=body.end_timestamp,
        title=_trim(body.title, TITLE_MAX_LENGTH),
        category=_optional(body.category, CATEGORY_MAX_LENGTH),
        description=_trim(body.description, DESCRIPTION_MAX_LENGTH),
        is_spoiler=body.is_spoiler,
        emotion=_optional(body.emotion, EMOTION_MAX_LENGTH),
    )


def map_delete_highlight_command(*, highlight_id: int, user_id: int) -> DeleteHighlightCommand:
    """Собрать команду удаления хайлайта.

    Args:
        highlight_id: Идентификатор хайлайта из пути.
        user_id: Идентификатор автора хайлайта.

    Returns:
        DeleteHighlightCommand: Команда удаления хайлайта.
    """
    return DeleteHighlightCommand(highlight_id=highlight_id, user_id=user_id)


def map_set_like_command(
    *,
    highlight_id: int,
    user_id: int,
    liked: bool,
) -> SetHighlightLikeCommand:
    """Собрать команду лайка по методу запроса.

    Args:
        highlight_id: Идентификатор хайлайта из пути.
        user_id: Идентификатор действующего пользователя.
        liked: True — поставить лайк, False — снять.

    Returns:
        SetHighlightLikeCommand: Команда изменения лайка.
    """
    return SetHighlightLikeCommand(highlight_id=highlight_id, user_id=user_id, liked=liked)


def map_set_saved_command(
    *,
    highlight_id: int,
    user_id: int,
    saved: bool,
) -> SetSavedHighlightCommand:
    """Собрать команду сохранения по методу запроса.

    Args:
        highlight_id: Идентификатор хайлайта из пути.
        user_id: Идентификатор действующего пользователя.
        saved: True — сохранить, False — убрать из сохранённых.

    Returns:
        SetSavedHighlightCommand: Команда изменения отметки сохранения.
    """
    return SetSavedHighlightCommand(highlight_id=highlight_id, user_id=user_id, saved=saved)


def map_add_comment_command(
    body: AddHighlightCommentRequest,
    *,
    highlight_id: int,
    user_id: int,
) -> AddHighlightCommentCommand:
    """Собрать команду добавления комментария из валидированного тела.

    Args:
        body: Разобранное и проверенное тело запроса.
        highlight_id: Идентификатор хайлайта из пути.
        user_id: Идентификатор автора комментария.

    Returns:
        AddHighlightCommentCommand: Команда добавления комментария.
    """
    return AddHighlightCommentCommand(
        highlight_id=highlight_id,
        user_id=user_id,
        content=_trim(body.content, DESCRIPTION_MAX_LENGTH),
    )


def map_dashboard_query(
    request: Request,
    *,
    user_id: int | None = None,
    viewer_user_id: int | None = None,
    include_spoilers_default: bool = False,
) -> HighlightDashboardQuery:
    """Собрать запрос сводки по параметрам строки запроса.

    Args:
        request: Текущий HTTP-запрос.
        user_id: Владелец личного дашборда либо None для публичных сводок.
        viewer_user_id: Идентификатор зрителя для отметок лайков и сохранений.
        include_spoilers_default: Показывать ли спойлеры при отсутствующем флаге запроса.

    Returns:
        HighlightDashboardQuery: Параметры дашборда.
    """
    params = request.query_params
    return HighlightDashboardQuery(
        anime_id=_to_int(params.get("anime_id")),
        emotion=_optional(params.get("emotion"), EMOTION_MAX_LENGTH),
        category=_optional(params.get("category"), CATEGORY_MAX_LENGTH),
        sort_by=_optional(params.get("sort"), SORT_MAX_LENGTH) or "recent",
        created_date=_optional(params.get("date"), DATE_MAX_LENGTH),
        query=_optional(params.get("query"), SEARCH_MAX_LENGTH),
        include_spoilers=not _to_bool(
            params.get("hide_spoilers"), default=not include_spoilers_default
        ),
        limit=_clamp_int(params.get("limit"), default=20, minimum=1, maximum=24),
        user_id=user_id,
        viewer_user_id=viewer_user_id,
    )


def map_feed_query(request: Request, *, viewer_user_id: int | None) -> HighlightFeedQuery:
    """Собрать запрос социальной ленты по параметрам строки запроса.

    Args:
        request: Текущий HTTP-запрос.
        viewer_user_id: Идентификатор зрителя для персональных секций.

    Returns:
        HighlightFeedQuery: Параметры ленты.
    """
    params = request.query_params
    return HighlightFeedQuery(
        anime_id=_to_int(params.get("anime_id")),
        category=_optional(params.get("category"), CATEGORY_MAX_LENGTH),
        include_spoilers=not _to_bool(params.get("hide_spoilers"), default=False),
        limit=_clamp_int(params.get("limit"), default=12, minimum=1, maximum=24),
        viewer_user_id=viewer_user_id,
    )


def _trim(value: object, max_length: int) -> str:
    """Очистить строку от пробелов и обрезать по длине.

    Args:
        value: Исходное значение любого типа.
        max_length: Максимальная длина результата.

    Returns:
        str: Обрезанная строка либо пустая строка.
    """
    return str(value or "").strip()[:max_length]


def _optional(value: object, max_length: int) -> str | None:
    """Вернуть необязательное значение либо None.

    Args:
        value: Исходное значение любого типа.
        max_length: Максимальная длина результата.

    Returns:
        str | None: Непустая строка после обрезки либо None.
    """
    cleaned = _trim(value, max_length)
    return cleaned or None


def _to_bool(value: object, *, default: bool) -> bool:
    """Преобразовать значение в булево.

    Args:
        value: Исходное значение любого типа.
        default: Значение при пустом или отсутствующем входе.

    Returns:
        bool: Истина для «1», «true», «yes» и «on».
    """
    if value in (None, ""):
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _to_int(value: object) -> int | None:
    """Преобразовать значение в целое число либо None.

    Args:
        value: Исходное значение любого типа.

    Returns:
        int | None: Число либо None при невозможном разборе.
    """
    if value in (None, ""):
        return None
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return None


def _clamp_int(value: object, *, default: int, minimum: int, maximum: int) -> int:
    """Ограничить целое число допустимым диапазоном.

    Args:
        value: Исходное значение любого типа.
        default: Значение при невозможном разборе.
        minimum: Нижняя граница результата.
        maximum: Верхняя граница результата.

    Returns:
        int: Число в диапазоне от нижней до верхней границы.
    """
    parsed = _to_int(value)
    if parsed is None:
        return default
    return max(min(parsed, maximum), minimum)
