from flask import (
    Blueprint,
    current_app,
    flash,
    g,
    render_template,
    request,
    redirect,
    url_for,
)

from src.backend.dependencies.container import container
from src.backend.infrastructure.security.flask_protection import (
    client_ip,
    rate_limit,
)
from src.backend.use_case.support.create_support_ticket import (
    InvalidSupportTicketError,
)

support_bp = Blueprint("support", __name__, url_prefix="/support")

SUPPORT_ATTEMPTS_LIMIT = 5
SUPPORT_WINDOW_SECONDS = 600


@support_bp.route("", methods=["GET"])
def support_page():
    """Рендерит страницу создания тикета поддержки."""
    return _render_support_page()


@support_bp.route("", methods=["POST"])
@rate_limit(
    container_getter=lambda: container,
    scope="support_ticket_create",
    limit=SUPPORT_ATTEMPTS_LIMIT,
    window_seconds=SUPPORT_WINDOW_SECONDS,
    key_builder=lambda: _support_attempt_subject(),
    response_mode="redirect",
    redirect_endpoint="support.support_page",
)
def create_support_ticket():
    """Создает тикет поддержки и отправляет его через выбранный канал."""
    user = getattr(g, "user", None)
    email = user.email if user else _normalize_email(request.form.get("email"))
    username = user.username if user else _normalize_username(request.form.get("username"))
    subject = request.form.get("subject", "")
    message = request.form.get("message", "")
    channel = _normalize_channel(request.form.get("channel"))
    page_url = request.form.get("page_url")

    try:
        ticket = container.create_support_ticket_use_case().execute(
            user_id=getattr(user, "id", None),
            email=email,
            username=username,
            subject=subject,
            message=message,
            channel=channel,
            page_url=page_url,
        )
    except InvalidSupportTicketError as error:
        flash(str(error))
        return _render_support_page(
            form_data=_build_form_data(
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
        current_app.logger.warning(
            "support_ticket_create_failed user_id=%s ip=%s",
            getattr(user, "id", None),
            client_ip(),
            exc_info=True,
        )
        flash("Не удалось создать тикет поддержки. Попробуй позже.")
        return _render_support_page(
            form_data=_build_form_data(
                email=email,
                username=username,
                subject=subject,
                message=message,
                channel=channel,
                page_url=page_url,
            ),
            status_code=500,
        )

    current_app.logger.info(
        "support_ticket_created ticket_id=%s user_id=%s delivery_status=%s ip=%s",
        ticket.id,
        ticket.user_id,
        ticket.delivery_status,
        client_ip(),
    )
    if ticket.delivery_status == "sent":
        if ticket.channel == "telegram":
            flash("Тикет отправлен в поддержку через Telegram.")
        else:
            flash("Тикет отправлен в поддержку по email.")
    else:
        if ticket.channel == "telegram":
            flash("Тикет сохранен, но Telegram сейчас недоступен. Поддержка сможет забрать его позже.")
        else:
            flash("Тикет сохранен, но email-канал сейчас недоступен. Поддержка сможет забрать его позже.")
    return redirect(url_for("support.support_page"))


def _render_support_page(
    form_data: dict[str, str] | None = None,
    status_code: int = 200,
):
    """Рендерит страницу поддержки с переданными значениями формы."""
    return (
        render_template(
            "support/create.html",
            support_form=form_data or _build_form_data(),
        ),
        status_code,
    )


def _build_form_data(
    email: str | None = None,
    username: str | None = None,
    subject: str | None = None,
    message: str | None = None,
    channel: str | None = None,
    page_url: str | None = None,
) -> dict[str, str]:
    """Формирует словарь значений для префилла support-формы."""
    user = getattr(g, "user", None)
    normalized_page_url = _normalize_page_url(page_url or request.args.get("page"))
    return {
        "email": _normalize_email(email or getattr(user, "email", "")),
        "username": _normalize_username(username or getattr(user, "username", "")),
        "subject": str(subject or "").strip(),
        "message": str(message or "").strip(),
        "channel": _normalize_channel(channel or request.args.get("channel")),
        "page_url": normalized_page_url,
    }


def _support_attempt_subject() -> str:
    """Строит ключ rate limit для создания support-тикета."""
    user = getattr(g, "user", None)
    if user and getattr(user, "id", None):
        return f"{client_ip()}::user::{user.id}"
    email = _normalize_email(request.form.get("email"))
    return f"{client_ip()}::guest::{email or 'anonymous'}"


def _normalize_email(value: str | None) -> str:
    """Нормализует email для формы поддержки."""
    return str(value or "").strip().lower()


def _normalize_username(value: str | None) -> str:
    """Нормализует username для формы поддержки."""
    return " ".join(str(value or "").strip().split())


def _normalize_page_url(value: str | None) -> str:
    """Ограничивает длину page_url в форме поддержки."""
    return str(value or "").strip()[:500]


def _normalize_channel(value: str | None) -> str:
    """Нормализует канал отправки support-тикета."""
    normalized = str(value or "").strip().lower()
    return normalized if normalized in {"telegram", "email"} else "telegram"
