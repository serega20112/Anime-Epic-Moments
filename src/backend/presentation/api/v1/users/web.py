"""Тонкие HTTP-маршруты публичных профилей и подписок (веб-формы).

Префикс ``/users`` несёт этот модуль: страница профиля и формы подписки
работают с редиректами и шаблонами, в отличие от JSON-API мобильного клиента.
"""

from __future__ import annotations

from http import HTTPStatus

from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from backend.application.dto import PublicProfileQuery, SetUserFollowCommand
from backend.application.use_cases import GetPublicProfileOverviewUseCase, SetUserFollowUseCase
from backend.presentation.api.helpers import get_current_user
from backend.presentation.api.rate_limit import client_ip, rate_limit
from backend.presentation.web import flash, render_template

user_router = APIRouter(prefix="/users", route_class=DishkaRoute)

NOT_FOUND_TEMPLATE = "errors/500_modal.html"
PUBLIC_PROFILE_TEMPLATE = "user/public_profile.html"
FOLLOW_FAILURE_MESSAGE = "Не удалось обновить подписку"


async def _follow_subject(request: Request) -> str:
    """Собрать составной ключ ограничения частоты для подписок.

    Args:
        request: Текущий HTTP-запрос.

    Returns:
        str: Ключ из адреса клиента и идентификатора зрителя.
    """
    ip = await client_ip(request)
    user_id = getattr(await get_current_user(request), "id", "guest")
    return f"{ip}::{user_id}"


async def _login_redirect(request: Request) -> RedirectResponse:
    """Собрать перенаправление на страницу входа.

    Args:
        request: Текущий HTTP-запрос.

    Returns:
        RedirectResponse: Перенаправление на страницу входа.
    """
    return RedirectResponse(
        url=request.app.url_path_for("auth.login_page"),
        status_code=HTTPStatus.SEE_OTHER,
    )


async def _profile_redirect(request: Request, user_id: int) -> RedirectResponse:
    """Собрать перенаправление назад в публичный профиль.

    Args:
        request: Текущий HTTP-запрос.
        user_id: Идентификатор профиля, куда возвращается зритель.

    Returns:
        RedirectResponse: Перенаправление на страницу профиля.
    """
    return RedirectResponse(
        url=request.app.url_path_for(
            "user.public_profile_page",
            user_id=str(user_id),
        ),
        status_code=HTTPStatus.SEE_OTHER,
    )


@user_router.get("/{user_id}", name="user.public_profile_page")
async def public_profile_page(
    request: Request,
    user_id: int,
    use_case: FromDishka[GetPublicProfileOverviewUseCase],
):
    """Отдать страницу публичного профиля пользователя.

    Args:
        request: Текущий HTTP-запрос.
        user_id: Идентификатор открываемого профиля.
        use_case: Сценарий сборки публичного профиля.

    Returns:
        Response: Страница профиля либо ошибка 404 при отсутствии пользователя.
    """
    viewer = await get_current_user(request)
    result = await use_case.execute(
        PublicProfileQuery(profile_user_id=user_id, viewer_user_id=viewer.id if viewer else None)
    )
    if not result.ok:
        return await render_template(request, NOT_FOUND_TEMPLATE, status_code=HTTPStatus.NOT_FOUND)
    return await render_template(
        request,
        PUBLIC_PROFILE_TEMPLATE,
        public_profile=result.data,
    )


@user_router.post("/{user_id}/follow", name="user.follow_user")
@rate_limit(
    scope="user_follow",
    limit=30,
    window_seconds=60,
    key_builder=_follow_subject,
)
async def follow_user(
    request: Request,
    user_id: int,
    use_case: FromDishka[SetUserFollowUseCase],
):
    """Подписаться на пользователя.

    Args:
        request: Текущий HTTP-запрос из формы профиля.
        user_id: Идентификатор целевого профиля.
        use_case: Сценарий изменения подписки.

    Returns:
        Response: Перенаправление в профиль либо на страницу входа.
    """
    return await _set_follow(request, user_id, follow=True, use_case=use_case)


@user_router.post("/{user_id}/unfollow", name="user.unfollow_user")
@rate_limit(
    scope="user_unfollow",
    limit=30,
    window_seconds=60,
    key_builder=_follow_subject,
)
async def unfollow_user(
    request: Request,
    user_id: int,
    use_case: FromDishka[SetUserFollowUseCase],
):
    """Отписаться от пользователя.

    Args:
        request: Текущий HTTP-запрос из формы профиля.
        user_id: Идентификатор целевого профиля.
        use_case: Сценарий изменения подписки.

    Returns:
        Response: Перенаправление в профиль либо на страницу входа.
    """
    return await _set_follow(request, user_id, follow=False, use_case=use_case)


async def _set_follow(
    request: Request,
    user_id: int,
    *,
    follow: bool,
    use_case: SetUserFollowUseCase,
):
    """Общий обработчик подписки и отписки формы публичного профиля.

    Args:
        request: Текущий HTTP-запрос.
        user_id: Идентификатор целевого профиля.
        follow: True — подписаться, False — отписаться.
        use_case: Сценарий изменения подписки.

    Returns:
        Response: Перенаправление в профиль либо на страницу входа.
    """
    viewer = await get_current_user(request)
    if not viewer:
        return await _login_redirect(request)
    result = await use_case.execute(
        SetUserFollowCommand(follower_user_id=viewer.id, followed_user_id=user_id, follow=follow)
    )
    if not result.ok:
        await flash(request, result.error or FOLLOW_FAILURE_MESSAGE)
    return await _profile_redirect(request, user_id)
