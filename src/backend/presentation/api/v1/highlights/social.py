"""Маршруты лайков, сохранений и комментариев хайлайтов."""

from __future__ import annotations

from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Request

from backend.application.dto import HighlightCommentsQuery, HighlightLikersQuery
from backend.application.use_cases import (
    AddHighlightCommentUseCase,
    GetHighlightLikersUseCase,
    SetHighlightLikeUseCase,
    SetSavedHighlightUseCase,
)
from backend.application.use_cases.highlight.social.get_highlight_comments import (
    GetHighlightCommentsUseCase,
)
from backend.presentation.api.errors import ErrorResponse, error_from_result, unauthorized_error
from backend.presentation.api.helpers import get_current_user
from backend.presentation.api.rate_limit import client_ip, rate_limit
from backend.presentation.api.requests.highlight_mapper import (
    map_add_comment_command,
    map_set_like_command,
    map_set_saved_command,
)
from backend.presentation.api.requests.highlight_requests import AddHighlightCommentRequest
from backend.presentation.api.responses.highlight_responses import (
    HighlightCommentResponse,
    HighlightCommentsResponse,
    HighlightLikeResponse,
    HighlightLikerResponse,
    HighlightLikersResponse,
    HighlightSavedResponse,
)
from backend.presentation.api.v1.highlights.helpers import read_limit

highlight_social_router = APIRouter(route_class=DishkaRoute)

_ERROR_RESPONSES = {
    "400": {"model": ErrorResponse},
    "401": {"model": ErrorResponse},
    "404": {"model": ErrorResponse},
    "429": {"model": ErrorResponse},
}


async def _highlight_subject(request: Request) -> str:
    """Собрать составной ключ ограничения частоты для социальных действий.

    Args:
        request: Текущий HTTP-запрос.

    Returns:
        str: Ключ из адреса клиента и идентификатора пользователя или слова ``guest``.
    """
    ip = await client_ip(request)
    user_id = getattr(await get_current_user(request), "id", "guest")
    return f"{ip}::{user_id}"


@highlight_social_router.get(
    "/{highlight_id}/likes",
    name="highlight.get_highlight_likes",
    response_model=HighlightLikersResponse,
    responses=_ERROR_RESPONSES,
)
@rate_limit(scope="highlight_like", limit=60, window_seconds=60, key_builder=_highlight_subject)
async def get_highlight_likes(
    request: Request,
    highlight_id: int,
    use_case: FromDishka[GetHighlightLikersUseCase],
):
    """Отдать список пользователей, лайкнувших хайлайт.

    Args:
        request: Текущий HTTP-запрос.
        highlight_id: Идентификатор хайлайта из пути.
        use_case: Сценарий чтения лайкнувших.

    Returns:
        HighlightLikersResponse: Пользователи в порядке последних лайков.
    """
    likers = await use_case.execute(
        HighlightLikersQuery(highlight_id=highlight_id, limit=read_limit(request, default=20))
    )
    return HighlightLikersResponse(
        items=[HighlightLikerResponse.model_validate(liker) for liker in likers]
    )


@highlight_social_router.post(
    "/{highlight_id}/likes",
    name="highlight.highlight_likes",
    response_model=HighlightLikeResponse,
    responses=_ERROR_RESPONSES,
)
@rate_limit(scope="highlight_like", limit=60, window_seconds=60, key_builder=_highlight_subject)
async def set_highlight_like(
    request: Request,
    highlight_id: int,
    use_case: FromDishka[SetHighlightLikeUseCase],
):
    """Поставить лайк хайлайту.

    Args:
        request: Текущий HTTP-запрос.
        highlight_id: Идентификатор хайлайта из пути.
        use_case: Сценарий установки лайка.

    Returns:
        HighlightLikeResponse: Итоговое состояние лайка либо тело ошибки.
    """
    return await _apply_like(request, highlight_id, use_case, liked=True)


@highlight_social_router.delete(
    "/{highlight_id}/likes",
    name="highlight.remove_highlight_like",
    response_model=HighlightLikeResponse,
    responses=_ERROR_RESPONSES,
)
@rate_limit(scope="highlight_like", limit=60, window_seconds=60, key_builder=_highlight_subject)
async def remove_highlight_like(
    request: Request,
    highlight_id: int,
    use_case: FromDishka[SetHighlightLikeUseCase],
):
    """Снять лайк с хайлайта.

    Args:
        request: Текущий HTTP-запрос.
        highlight_id: Идентификатор хайлайта из пути.
        use_case: Сценарий установки лайка.

    Returns:
        HighlightLikeResponse: Итоговое состояние лайка либо тело ошибки.
    """
    return await _apply_like(request, highlight_id, use_case, liked=False)


@highlight_social_router.post(
    "/{highlight_id}/save",
    name="highlight.set_saved_highlight",
    response_model=HighlightSavedResponse,
    responses=_ERROR_RESPONSES,
)
@rate_limit(scope="highlight_save", limit=60, window_seconds=60, key_builder=_highlight_subject)
async def set_saved_highlight(
    request: Request,
    highlight_id: int,
    use_case: FromDishka[SetSavedHighlightUseCase],
):
    """Сохранить хайлайт в личную коллекцию.

    Args:
        request: Текущий HTTP-запрос.
        highlight_id: Идентификатор хайлайта из пути.
        use_case: Сценарий сохранения хайлайта.

    Returns:
        HighlightSavedResponse: Итоговое состояние сохранения либо тело ошибки.
    """
    return await _apply_save(request, highlight_id, use_case, saved=True)


@highlight_social_router.delete(
    "/{highlight_id}/save",
    name="highlight.unset_saved_highlight",
    response_model=HighlightSavedResponse,
    responses=_ERROR_RESPONSES,
)
@rate_limit(scope="highlight_save", limit=60, window_seconds=60, key_builder=_highlight_subject)
async def unset_saved_highlight(
    request: Request,
    highlight_id: int,
    use_case: FromDishka[SetSavedHighlightUseCase],
):
    """Убрать хайлайт из личной коллекции.

    Args:
        request: Текущий HTTP-запрос.
        highlight_id: Идентификатор хайлайта из пути.
        use_case: Сценарий сохранения хайлайта.

    Returns:
        HighlightSavedResponse: Итоговое состояние сохранения либо тело ошибки.
    """
    return await _apply_save(request, highlight_id, use_case, saved=False)


@highlight_social_router.get(
    "/{highlight_id}/comments",
    name="highlight.get_highlight_comments",
    response_model=HighlightCommentsResponse,
    responses=_ERROR_RESPONSES,
)
@rate_limit(scope="highlight_comment", limit=30, window_seconds=60, key_builder=_highlight_subject)
async def get_highlight_comments(
    request: Request,
    highlight_id: int,
    use_case: FromDishka[GetHighlightCommentsUseCase],
):
    """Отдать комментарии хайлайта.

    Args:
        request: Текущий HTTP-запрос.
        highlight_id: Идентификатор хайлайта из пути.
        use_case: Сценарий чтения комментариев.

    Returns:
        HighlightCommentsResponse: Комментарии в порядке добавления.
    """
    comments = await use_case.execute(
        HighlightCommentsQuery(highlight_id=highlight_id, limit=read_limit(request, default=20))
    )
    return HighlightCommentsResponse(
        items=[HighlightCommentResponse.model_validate(comment) for comment in comments]
    )


@highlight_social_router.post(
    "/{highlight_id}/comments",
    name="highlight.highlight_comments",
    response_model=HighlightCommentResponse,
    responses=_ERROR_RESPONSES,
)
@rate_limit(scope="highlight_comment", limit=30, window_seconds=60, key_builder=_highlight_subject)
async def add_highlight_comment(
    request: Request,
    highlight_id: int,
    body: AddHighlightCommentRequest,
    use_case: FromDishka[AddHighlightCommentUseCase],
):
    """Добавить комментарий к хайлайту.

    Args:
        request: Текущий HTTP-запрос.
        highlight_id: Идентификатор хайлайта из пути.
        body: Проверенное тело комментария.
        use_case: Сценарий добавления комментария.

    Returns:
        HighlightCommentResponse: Созданный комментарий либо тело ошибки.
    """
    user = await get_current_user(request)
    if not user:
        return unauthorized_error()
    result = await use_case.execute(
        map_add_comment_command(body, highlight_id=highlight_id, user_id=user.id)
    )
    if not result.ok:
        return error_from_result(result)
    return HighlightCommentResponse.model_validate(result.data)


async def _apply_like(
    request: Request,
    highlight_id: int,
    use_case: SetHighlightLikeUseCase,
    *,
    liked: bool,
):
    """Выполнить команду лайка и собрать ответ.

    Args:
        request: Текущий HTTP-запрос.
        highlight_id: Идентификатор хайлайта из пути.
        use_case: Сценарий установки лайка.
        liked: True — поставить лайк, False — снять.

    Returns:
        HighlightLikeResponse: Итоговое состояние лайка либо тело ошибки.
    """
    user = await get_current_user(request)
    if not user:
        return unauthorized_error()
    result = await use_case.execute(
        map_set_like_command(highlight_id=highlight_id, user_id=user.id, liked=liked)
    )
    if not result.ok:
        return error_from_result(result)
    return HighlightLikeResponse(
        highlight_id=highlight_id,
        liked=liked,
        likes_count=getattr(result.data, "likes_count", 0),
    )


async def _apply_save(
    request: Request,
    highlight_id: int,
    use_case: SetSavedHighlightUseCase,
    *,
    saved: bool,
):
    """Выполнить команду сохранения и собрать ответ.

    Args:
        request: Текущий HTTP-запрос.
        highlight_id: Идентификатор хайлайта из пути.
        use_case: Сценарий сохранения хайлайта.
        saved: True — сохранить, False — убрать из сохранённых.

    Returns:
        HighlightSavedResponse: Итоговое состояние сохранения либо тело ошибки.
    """
    user = await get_current_user(request)
    if not user:
        return unauthorized_error()
    result = await use_case.execute(
        map_set_saved_command(highlight_id=highlight_id, user_id=user.id, saved=saved)
    )
    if not result.ok:
        return error_from_result(result)
    return HighlightSavedResponse(highlight_id=highlight_id, saved=bool(result.data))
