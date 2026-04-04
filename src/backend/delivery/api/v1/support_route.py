import logging

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from src.backend.delivery.api.helpers import get_container, get_current_user
from src.backend.infrastructure.security.flask_protection import client_ip, rate_limit
from src.backend.infrastructure.web.templating import flash, render_template
from src.backend.use_case.support.create_support_ticket import InvalidSupportTicketError

support_router = APIRouter(prefix="/support")
support_bp = support_router
container = None
logger = logging.getLogger("anime_epic_moments")

SUPPORT_ATTEMPTS_LIMIT = 5
SUPPORT_WINDOW_SECONDS = 600


@support_router.get("", name="support.support_page")
async def support_page(request: Request):
    return _render_support_page(request)


@support_router.post("", name="support.create_support_ticket")
@rate_limit(
    scope="support_ticket_create",
    limit=SUPPORT_ATTEMPTS_LIMIT,
    window_seconds=SUPPORT_WINDOW_SECONDS,
    key_builder=lambda request: _support_attempt_subject(request),
    response_mode="redirect",
    redirect_endpoint="support.support_page",
)
async def create_support_ticket(request: Request):
    container = get_container(request)
    user = get_current_user(request)
    form = await request.form()
    email = user.email if user else _normalize_email(form.get("email"))
    username = user.username if user else _normalize_username(form.get("username"))
    subject = form.get("subject", "")
    message = form.get("message", "")
    channel = _normalize_channel(form.get("channel"))
    page_url = form.get("page_url")

    try:
        ticket = await container.create_support_ticket_use_case().execute(
            user_id=getattr(user, "id", None),
            email=email,
            username=username,
            subject=subject,
            message=message,
            channel=channel,
            page_url=page_url,
        )
    except InvalidSupportTicketError as error:
        flash(request, str(error))
        return _render_support_page(
            request,
            form_data=_build_form_data(
                request,
                email=email,
                username=username,
                subject=subject,
                message=message,
                channel=channel,
                page_url=page_url,
            ),
            status_code=400,
        )
    except Exception:
        logger.warning(
            "support_ticket_create_failed user_id=%s ip=%s",
            getattr(user, "id", None),
            client_ip(request),
            exc_info=True,
        )
        flash(request, "Не удалось создать тикет поддержки. Попробуй позже.")
        return _render_support_page(
            request,
            form_data=_build_form_data(
                request,
                email=email,
                username=username,
                subject=subject,
                message=message,
                channel=channel,
                page_url=page_url,
            ),
            status_code=500,
        )

    logger.info(
        "support_ticket_created ticket_id=%s user_id=%s delivery_status=%s ip=%s",
        ticket.id,
        ticket.user_id,
        ticket.delivery_status,
        client_ip(request),
    )
    if ticket.delivery_status == "sent":
        flash(
            request,
            "Тикет отправлен в поддержку через Telegram."
            if ticket.channel == "telegram"
            else "Тикет отправлен в поддержку по email.",
        )
    else:
        flash(
            request,
            "Тикет сохранен, но Telegram сейчас недоступен. Поддержка сможет забрать его позже."
            if ticket.channel == "telegram"
            else "Тикет сохранен, но email-канал сейчас недоступен. Поддержка сможет забрать его позже.",
        )
    return RedirectResponse(
        url=request.app.url_path_for("support.support_page"),
        status_code=303,
    )


def _render_support_page(
    request: Request,
    form_data: dict[str, str] | None = None,
    status_code: int = 200,
):
    return render_template(
        request,
        "support/create.html",
        support_form=form_data or _build_form_data(request),
        status_code=status_code,
    )


def _build_form_data(
    request: Request,
    email: str | None = None,
    username: str | None = None,
    subject: str | None = None,
    message: str | None = None,
    channel: str | None = None,
    page_url: str | None = None,
) -> dict[str, str]:
    user = get_current_user(request)
    normalized_page_url = _normalize_page_url(
        page_url or request.query_params.get("page")
    )
    return {
        "email": _normalize_email(email or getattr(user, "email", "")),
        "username": _normalize_username(username or getattr(user, "username", "")),
        "subject": str(subject or "").strip(),
        "message": str(message or "").strip(),
        "channel": _normalize_channel(channel or request.query_params.get("channel")),
        "page_url": normalized_page_url,
    }


def _support_attempt_subject(request: Request) -> str:
    user = get_current_user(request)
    if user and getattr(user, "id", None):
        return f"{client_ip(request)}::user::{user.id}"
    return f"{client_ip(request)}::guest"


def _normalize_email(value: str | None) -> str:
    return str(value or "").strip().lower()


def _normalize_username(value: str | None) -> str:
    return " ".join(str(value or "").strip().split())


def _normalize_page_url(value: str | None) -> str:
    return str(value or "").strip()[:500]


def _normalize_channel(value: str | None) -> str:
    normalized = str(value or "").strip().lower()
    return normalized if normalized in {"telegram", "email"} else "telegram"
