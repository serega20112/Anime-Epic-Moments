"""Маршруты запроса и подтверждения сброса пароля."""

from __future__ import annotations

from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Request

from backend.application.use_cases.auth.password_reset.request_password_reset import (
    RequestPasswordResetUseCase,
)
from backend.application.use_cases.auth.password_reset.reset_password import (
    ResetPasswordUseCase,
)
from backend.presentation.api.auth_responses import (
    redirect,
    redirect_confirm,
    resolve,
)
from backend.presentation.api.requests.auth_mapper import (
    FormValidationError,
    map_confirm_password_reset_command,
    map_request_password_reset_command,
)
from backend.presentation.dependencies.client_ip import client_ip
from backend.presentation.web import render_template
from backend.utils import log_security_event

password_reset_router = APIRouter(route_class=DishkaRoute)


@password_reset_router.get("/password-reset", name="auth.password_reset_request_page")
async def password_reset_request_page(request: Request):
    """Отдать страницу запроса сброса пароля."""
    return await render_template(request, "auth/password_reset_request.html")


@password_reset_router.get(
    "/password-reset/confirm",
    name="auth.password_reset_confirm_page",
)
async def password_reset_confirm_page(request: Request):
    """Отдать страницу подтверждения сброса пароля."""
    token = str(request.query_params.get("token", ""))
    return await render_template(request, "auth/password_reset_confirm.html", token=token)


@password_reset_router.post("/password-reset", name="auth.request_password_reset")
async def request_password_reset(
    request: Request,
    use_case: FromDishka[RequestPasswordResetUseCase],
):
    """Отправить письмо со ссылкой сброса пароля."""
    form = await request.form()
    try:
        command = map_request_password_reset_command(
            form, base_url=str(request.base_url).rstrip("/")
        )
    except FormValidationError:
        return await redirect(request, "auth.password_reset_request_page")
    log_security_event(
        event="password_reset_requested",
        email=command.email,
        ip_address=await client_ip(request),
    )
    await use_case.execute(command)
    return await redirect(request, "auth.password_reset_request_page")


@password_reset_router.post("/password-reset/confirm", name="auth.confirm_password_reset")
async def confirm_password_reset(request: Request, use_case: FromDishka[ResetPasswordUseCase]):
    """Подтвердить сброс пароля по токену и новому паролю."""
    form = await request.form()
    try:
        command = map_confirm_password_reset_command(form)
    except FormValidationError as error:
        return await redirect_confirm(request, str(error))
    log_security_event(event="password_reset_success", ip_address=await client_ip(request))
    result = await use_case.execute(command)
    return await resolve(request, result)
