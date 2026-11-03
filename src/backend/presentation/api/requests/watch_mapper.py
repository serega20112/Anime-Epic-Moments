"""Преобразователи запросов для команд просмотра."""

from __future__ import annotations

from fastapi import Request

from backend.application.dto import (
    AddAnimeCommentCommand,
    AddWatchSourceCommand,
    CompleteEpisodeCommand,
    CreateWatchHighlightCommand,
    SaveViewingSessionCommand,
    SetAnimeCommentLikeCommand,
    SyncWatchSourcesQuery,
    UpsertUserAnimeStatusCommand,
    WatchPageQuery,
)
from backend.presentation.api.requests.watch_requests import (
    CATEGORY_MAX_LENGTH,
    EMOTION_MAX_LENGTH,
    PROVIDER_MAX_LENGTH,
    QUALITY_MAX_LENGTH,
    STREAM_URL_MAX_LENGTH,
    TITLE_MAX_LENGTH,
    TRANSLATION_MAX_LENGTH,
    AddAnimeCommentRequest,
    AddWatchSourceRequest,
    CompleteEpisodeRequest,
    CreateWatchHighlightRequest,
    DiscoverSourcesRequest,
    SaveProgressRequest,
    SaveViewingSessionRequest,
    UpdateWatchStatusRequest,
)

DESCRIPTION_MAX_LENGTH = 600
SORT_MAX_LENGTH = 20
DEFAULT_EPISODE = 1


def map_watch_page_query(
    request: Request,
    *,
    anime_id: int,
    user_id: int | None,
) -> WatchPageQuery:
    """Собрать запрос страницы просмотра из параметров строки запроса.

    Args:
        request: Текущий HTTP-запрос.
        anime_id: Идентификатор аниме из пути.
        user_id: Идентификатор зрителя либо None для гостя.

    Returns:
        WatchPageQuery: Параметры сборки страницы.
    """
    params = request.query_params
    return WatchPageQuery(
        anime_id=anime_id,
        episode=_to_int(params.get("episode")) or DEFAULT_EPISODE,
        selected_source_id=_to_int(params.get("source_id")),
        preferred_start_seconds=_to_float(params.get("start_at")),
        discussion_sort=_optional(params.get("discussion_sort"), SORT_MAX_LENGTH) or "popular",
        user_id=user_id,
    )


def map_sync_sources_query(
    body: DiscoverSourcesRequest,
    *,
    anime_id: int,
) -> SyncWatchSourcesQuery:
    """Собрать запрос поиска источников из валидированного тела.

    Args:
        body: Разобранное тело запроса поиска источников.
        anime_id: Идентификатор аниме из пути.

    Returns:
        SyncWatchSourcesQuery: Параметры синхронизации с принудительным обновлением.
    """
    return SyncWatchSourcesQuery(
        anime_id=anime_id,
        episode=body.episode or DEFAULT_EPISODE,
        force=True,
    )


def map_upsert_status_command(
    body: UpdateWatchStatusRequest,
    *,
    user_id: int,
    anime_id: int,
) -> UpsertUserAnimeStatusCommand:
    """Собрать команду обновления статуса из валидированного тела.

    Args:
        body: Разобранное тело статуса просмотра.
        user_id: Идентификатор действующего пользователя.
        anime_id: Идентификатор аниме из пути.

    Returns:
        UpsertUserAnimeStatusCommand: Команда upsert статуса.
    """
    return UpsertUserAnimeStatusCommand(
        user_id=user_id,
        anime_id=anime_id,
        status=body.status.strip(),
    )


def map_save_session_command(
    body: SaveViewingSessionRequest,
    *,
    user_id: int,
    anime_id: int,
) -> SaveViewingSessionCommand:
    """Собрать команду сохранения сессии из валидированного тела.

    Args:
        body: Разобранное тело состояния плеера.
        user_id: Идентификатор действующего пользователя.
        anime_id: Идентификатор аниме из пути.

    Returns:
        SaveViewingSessionCommand: Команда сохранения сессии просмотра.
    """
    return SaveViewingSessionCommand(
        user_id=user_id,
        anime_id=anime_id,
        episode=body.episode,
        watch_source_id=body.watch_source_id,
        position_seconds=body.position_seconds,
        volume=body.volume,
        quality_label=body.quality_label.strip() or "Auto",
        is_paused=body.is_paused,
    )


def map_save_progress_command(
    body: SaveProgressRequest,
    *,
    user_id: int,
    anime_id: int,
) -> SaveViewingSessionCommand:
    """Собрать команду сохранения позиции из тела мобильного прогресса.

    Длительность серии в команду не входит: она нужна лишь presentation-
    решению о пороге «просмотрено», а сценарий сохраняет позицию и состояние
    плеера.

    Args:
        body: Разобранное тело позиции мобильного плеера.
        user_id: Идентификатор действующего пользователя.
        anime_id: Идентификатор аниме из пути.

    Returns:
        SaveViewingSessionCommand: Команда сохранения сессии просмотра.
    """
    return SaveViewingSessionCommand(
        user_id=user_id,
        anime_id=anime_id,
        episode=body.episode,
        watch_source_id=body.watch_source_id,
        position_seconds=body.position_seconds,
        volume=body.volume,
        quality_label=body.quality_label.strip() or "Auto",
        is_paused=body.is_paused,
    )


def map_complete_episode_command(
    body: CompleteEpisodeRequest,
    *,
    user_id: int,
    anime_id: int,
) -> CompleteEpisodeCommand:
    """Собрать команду завершения серии из валидированного тела.

    Args:
        body: Разобранное тело номера серии.
        user_id: Идентификатор действующего пользователя.
        anime_id: Идентификатор аниме из пути.

    Returns:
        CompleteEpisodeCommand: Команда отметки просмотренной серии.
    """
    return CompleteEpisodeCommand(user_id=user_id, anime_id=anime_id, episode=body.episode)


def map_create_watch_highlight_command(
    body: CreateWatchHighlightRequest,
    *,
    user_id: int,
    anime_id: int,
) -> CreateWatchHighlightCommand:
    """Собрать команду создания хайлайта из плеера из валидированного тела.

    Args:
        body: Разобранное тело хайлайта с контекстом плеера.
        user_id: Идентификатор владельца хайлайта.
        anime_id: Идентификатор аниме из пути.

    Returns:
        CreateWatchHighlightCommand: Команда создания хайлайта.
    """
    return CreateWatchHighlightCommand(
        user_id=user_id,
        anime_id=anime_id,
        episode=body.episode,
        title=_trim(body.title, TITLE_MAX_LENGTH),
        category=_optional(body.category, CATEGORY_MAX_LENGTH),
        start_timestamp=body.start_timestamp,
        end_timestamp=body.end_timestamp,
        description=_trim(body.description, DESCRIPTION_MAX_LENGTH),
        is_spoiler=body.is_spoiler,
        emotion=_optional(body.emotion, EMOTION_MAX_LENGTH),
        watch_source_id=body.watch_source_id,
        translation_id=body.translation_id,
        original_title=_optional(body.original_title, TITLE_MAX_LENGTH),
    )


def map_add_anime_comment_command(
    body: AddAnimeCommentRequest,
    *,
    anime_id: int,
    user_id: int,
) -> AddAnimeCommentCommand:
    """Собрать команду комментария к аниме из валидированного тела.

    Args:
        body: Разобранное тело комментария.
        anime_id: Идентификатор аниме из пути.
        user_id: Идентификатор автора комментария.

    Returns:
        AddAnimeCommentCommand: Команда добавления комментария.
    """
    return AddAnimeCommentCommand(
        anime_id=anime_id,
        user_id=user_id,
        content=_trim(body.content, DESCRIPTION_MAX_LENGTH),
    )


def map_add_watch_source_command(
    body: AddWatchSourceRequest, *, anime_id: int
) -> AddWatchSourceCommand:
    """Собрать команду ручного добавления источника из валидированного тела.

    Args:
        body: Разобранное тело источника просмотра.
        anime_id: Идентификатор аниме из пути.

    Returns:
        AddWatchSourceCommand: Команда создания озвучки и источника.
    """
    return AddWatchSourceCommand(
        anime_id=anime_id,
        episode=body.episode,
        translation_name=_trim(body.translation_name, TRANSLATION_MAX_LENGTH),
        translation_type=_trim(body.translation_type, PROVIDER_MAX_LENGTH),
        provider_name=_trim(body.provider_name, PROVIDER_MAX_LENGTH),
        source_name=_trim(body.source_name, TITLE_MAX_LENGTH),
        stream_url=_trim(body.stream_url, STREAM_URL_MAX_LENGTH),
        quality_label=_trim(body.quality_label, QUALITY_MAX_LENGTH) or "Auto",
        language=body.language,
        source_type=body.source_type,
    )


def map_set_comment_like_command(
    *,
    comment_id: int,
    user_id: int,
    liked: bool,
) -> SetAnimeCommentLikeCommand:
    """Собрать команду лайка комментария по методу запроса.

    Args:
        comment_id: Идентификатор комментария из пути.
        user_id: Идентификатор действующего пользователя.
        liked: True — поставить лайк, False — снять.

    Returns:
        SetAnimeCommentLikeCommand: Команда изменения лайка комментария.
    """
    return SetAnimeCommentLikeCommand(comment_id=comment_id, user_id=user_id, liked=liked)


def _trim(value: str, max_length: int) -> str:
    """Очистить строку от пробелов и обрезать по длине.

    Args:
        value: Исходное значение.
        max_length: Максимальная длина результата.

    Returns:
        str: Обрезанная строка.
    """
    return str(value or "").strip()[:max_length]


def _optional(value: str | None, max_length: int) -> str | None:
    """Вернуть необязательное значение либо None.

    Args:
        value: Исходное значение.
        max_length: Максимальная длина результата.

    Returns:
        str | None: Непустая строка после обрезки либо None.
    """
    cleaned = _trim(value, max_length)
    return cleaned or None


def _to_int(value: str | None) -> int | None:
    """Преобразовать параметр строки запроса в целое число либо None.

    Args:
        value: Исходное текстовое значение.

    Returns:
        int | None: Число либо None при невозможном разборе.
    """
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return None


def _to_float(value: str | None) -> float | None:
    """Преобразовать параметр строки запроса в дробное число либо None.

    Args:
        value: Исходное текстовое значение.

    Returns:
        float | None: Число либо None при невозможном разборе.
    """
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return None
