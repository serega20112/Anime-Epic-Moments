"""Маршруты страницы поддержки и создания обращений.

Префикс ``/support`` несёт сам модуль: корневая страница объявлена пустым путём,
который FastAPI не допускает на роутере без префикса.
"""

from __future__ import annotations

from http import HTTPStatus

from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from backend.application.use_cases import CreateSupportTicketUseCase
from backend.config import Settings
from backend.presentation.api.helpers import get_current_user
from backend.presentation.api.rate_limit import client_ip, rate_limit
from backend.presentation.api.requests.support_form_builder import (
    build_default_support_form,
    build_support_form_data,
)
from backend.presentation.api.requests.support_mapper import map_create_support_ticket_command
from backend.presentation.dependencies.rate_limit_keys import support_ticket_subject
from backend.presentation.web import flash, render_template
from backend.utils import log_business_event

tickets_router = APIRouter(prefix="/support", route_class=DishkaRoute)

SUPPORT_TEMPLATE = "support/create.html"
CREATE_FAILURE_MESSAGE = "Не удалось создать тикет поддержки"
CREATE_SUCCESS_MESSAGE = "Тикет отправлен в поддержку."


async def _support_ticket_subject(request: Request) -> str:
    """Собрать составной ключ ограничения частоты для создания обращения.

    Args:
        request: Текущий HTTP-запрос.

    Returns:
        str: Ключ из адреса клиента и идентификатора автора.
    """
    return await support_ticket_subject(
        ip_address=await client_ip(request),
        user_id=getattr(await get_current_user(request), "id", None),
    )


@tickets_router.get("", name="support.support_page")
async def support_page(request: Request):
    """Отдать страницу создания обращения в поддержку.

    Args:
        request: Текущий HTTP-запрос.

    Returns:
        Response: Отрисованная форма обращения с предзаполнением по умолчанию.
    """
    return await _render_support_page(request)


@tickets_router.post("", name="support.create_support_ticket")
@rate_limit(
    scope="support_ticket_create",
    limit=Settings.support_ticket_rate_limit,
    window_seconds=Settings.auth_window_seconds,
    key_builder=_support_ticket_subject,
    response_mode="redirect",
    redirect_endpoint="support.support_page",
)
async def create_support_ticket(
    request: Request,
    use_case: FromDishka[CreateSupportTicketUseCase],
):
    """Создать обращение в поддержку из данных формы.

    Args:
        request: Текущий HTTP-запрос с телом HTML-формы.
        use_case: Сценарий создания обращения.

    Returns:
        Response: Перенаправление на страницу поддержки либо форма с ошибками.
    """
    user = await get_current_user(request)
    user_id = getattr(user, "id", None)
    command = map_create_support_ticket_command(
        dict(await request.form()),
        user_id=user_id,
        user_email=getattr(user, "email", None),
        user_username=getattr(user, "username", None),
    )
    result = await use_case.execute(command)

    if not result.ok:
        await flash(request, result.error_message or CREATE_FAILURE_MESSAGE)
        return await _render_support_page(
            request,
            form_data=build_support_form_data(
                command=command,
                user_email=getattr(user, "email", None),
                user_username=getattr(user, "username", None),
            ),
            status_code=result.status_code,
        )

    ticket = result.data
    log_business_event(
        event="support_ticket_created",
        user_id=ticket.user_id,
        ip_address=await client_ip(request),
        details={
            "ticket_id": getattr(ticket, "id", None),
            "delivery_status": ticket.delivery_status,
        },
    )
    await flash(request, result.message or CREATE_SUCCESS_MESSAGE)
    return RedirectResponse(
        url=request.app.url_path_for("support.support_page"),
        status_code=HTTPStatus.SEE_OTHER,
    )


async def _render_support_page(
    request: Request,
    form_data: dict[str, str] | None = None,
    status_code: int = HTTPStatus.OK,
):
    """Отдать страницу поддержки с данными формы.

    Args:
        request: Текущий HTTP-запрос.
        form_data: Поля для повторного показа либо None для предзаполнения по умолчанию.
        status_code: HTTP-код ответа страницы.

    Returns:
        Response: Отрисованная форма обращения.
    """
    return await render_template(
        request,
        SUPPORT_TEMPLATE,
        support_form=form_data or await _default_form(request),
        status_code=status_code,
    )


async def _default_form(request: Request) -> dict[str, str]:
    """Собрать данные формы по умолчанию для страницы поддержки.

    Args:
        request: Текущий HTTP-запрос с параметрами ``channel`` и ``page``.

    Returns:
        dict[str, str]: Предзаполненные поля формы обращения.
    """
    user = await get_current_user(request)
    return build_default_support_form(
        user_email=getattr(user, "email", ""),
        user_username=getattr(user, "username", ""),
        channel_param=request.query_params.get("channel"),
        page_param=request.query_params.get("page"),
    )
