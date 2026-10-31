"""Маршруты профиля авторизованного пользователя."""

from __future__ import annotations

from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Request

from backend.application.dto import ProfileOverviewQuery
from backend.application.interface.services import ImageStorageError, ImageStoragePort
from backend.application.use_cases.auth.profile.get_profile_overview import (
    GetProfileOverviewUseCase,
)
from backend.application.use_cases.auth.profile.update_user_profile import (
    UpdateUserProfileUseCase,
)
from backend.presentation.api.auth_responses import redirect, resolve
from backend.presentation.api.requests.auth_mapper import map_update_profile_command
from backend.presentation.web import flash, render_template

profile_router = APIRouter(route_class=DishkaRoute)


@profile_router.get("/profile", name="auth.profile_page")
async def profile_page(request: Request, use_case: FromDishka[GetProfileOverviewUseCase]):
    """Отдать страницу профиля авторизованного пользователя.

    Args:
        request: Текущий HTTP-запрос.
        use_case: Сценарий обзора профиля.

    Returns:
        Response: Страница профиля либо редирект на вход для гостя.
    """
    user = getattr(request.state, "user", None)
    if not user:
        return await redirect(request, "auth.login_page")
    overview = await use_case.execute(ProfileOverviewQuery(user_id=user.id))
    return await render_template(
        request,
        "auth/profile.html",
        profile_user=user,
        profile_overview=overview,
    )


@profile_router.post("/profile", name="auth.update_profile")
async def update_profile(
    request: Request,
    use_case: FromDishka[UpdateUserProfileUseCase],
    storage: FromDishka[ImageStoragePort],
):
    """Обновляет профиль авторизованного пользователя.

    Args:
        request: Текущий HTTP-запрос с формой профиля.
        use_case: Сценарий обновления профиля.
        storage: Хранилище загруженного аватара.

    Returns:
        Response: Редирект на страницу профиля либо на вход для гостя.
    """
    user = getattr(request.state, "user", None)
    if not user:
        return await redirect(request, "auth.login_page")
    form = await request.form()
    avatar_url, avatar_rejected = await _store_avatar(request, form, storage)
    if avatar_rejected:
        return await redirect(request, "auth.profile_page")
    result = await use_case.execute(
        map_update_profile_command(form, user_id=user.id, uploaded_avatar_url=avatar_url)
    )
    return await resolve(request, result)


async def _store_avatar(
    request: Request, form, storage: ImageStoragePort
) -> tuple[str | None, bool]:
    """Сохранить файл аватара, если он пришёл вместе с формой.

    Args:
        request: Текущий HTTP-запрос — нужен для flash-сообщения об отказе.
        form: Разобранные данные формы профиля.
        storage: Хранилище изображений.

    Returns:
        tuple[str | None, bool]: Адрес сохранённого аватара (либо None) и признак
            того, что загрузку отклонили.
    """
    upload = form.get("avatar_url")
    if not getattr(upload, "filename", None):
        return None, False
    try:
        return await storage.save(upload, "avatars"), False
    except ImageStorageError as error:
        await flash(request, str(error))
        return None, True
