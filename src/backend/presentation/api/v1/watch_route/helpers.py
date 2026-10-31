"""Общие помощники HTTP-маршрутов просмотра."""

from __future__ import annotations

from fastapi import Request

from backend.domain.value_objects.anime.discussion import AnimeDiscussionComment
from backend.presentation.api.errors import ErrorResponse
from backend.presentation.api.helpers import get_current_user
from backend.presentation.api.rate_limit import client_ip
from backend.presentation.api.responses.watch_responses import AnimeCommentResponse
from backend.presentation.dependencies.rate_limit_keys import (
    watch_anime_subject,
    watch_user_subject,
)

DISCUSSION_PREVIEW_LIMIT = 20
MANUAL_SOURCE_DISABLED_CODE = "manual_source_creation_disabled"
MANUAL_SOURCE_DISABLED_MESSAGE = "Ручное добавление источников отключено"

ERROR_RESPONSES = {
    "400": {"model": ErrorResponse},
    "401": {"model": ErrorResponse},
    "404": {"model": ErrorResponse},
    "429": {"model": ErrorResponse},
}


async def discover_sources_subject(request: Request) -> str:
    """Собрать составной ключ ограничения частоты для поиска источников.

    Args:
        request: Текущий HTTP-запрос.

    Returns:
        str: Ключ из адреса клиента и идентификатора аниме.
    """
    return await watch_anime_subject(
        ip_address=await client_ip(request),
        anime_id=request.path_params.get("anime_id"),
    )


async def create_watch_highlight_subject(request: Request) -> str:
    """Собрать составной ключ ограничения частоты для хайлайта из плеера.

    Args:
        request: Текущий HTTP-запрос.

    Returns:
        str: Ключ из адреса клиента и идентификатора пользователя.
    """
    return await watch_user_subject(
        ip_address=await client_ip(request),
        user_id=getattr(await get_current_user(request), "id", None),
    )


def comment_response(comment: AnimeDiscussionComment) -> AnimeCommentResponse:
    """Собрать JSON-представление комментария обсуждения.

    Args:
        comment: Комментарий, возвращённый сценарием.

    Returns:
        AnimeCommentResponse: Готовый ответ маршрута обсуждения.
    """
    return AnimeCommentResponse.model_validate(comment)
