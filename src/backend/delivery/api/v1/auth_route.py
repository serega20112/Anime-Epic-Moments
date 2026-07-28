import logging
from http import HTTPStatus

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, RedirectResponse

from src.backend.dependencies.settings import Settings
from src.backend.delivery.api.helpers import get_container, get_current_user
from src.backend.infrastructure.security.flask_protection import client_ip, rate_limit
from src.backend.infrastructure.security.account_lock_service import AccountLockService
from src.backend.infrastructure.web.templating import flash, render_template
from src.backend.infrastructure.security.jwt_service import JWTService
from src.backend.use_case.auth.login_user import InvalidCredentialsError
from src.backend.use_case.auth.register_user import EmailAlreadyExistsError
from src.backend.use_case.auth.resend_email_verification import (
    PendingEmailVerificationNotFoundError,
)
from src.backend.use_case.auth.reset_password import InvalidPasswordResetTokenError
from src.backend.use_case.auth.update_user_profile import (
    InvalidProfileDataError,
    UserNotFoundError,
)
from src.backend.use_case.auth.verify_email import (
    EmailVerificationExpiredError,
    InvalidEmailVerificationCodeError,
)

auth_router = APIRouter(prefix="/auth")
auth_bp = auth_router
container = None
logger = logging.getLogger("anime_epic_moments")

jwt_service = JWTService()


@auth_router.get("/login", name="auth.login_page")
async def login_page(request: Request):
    return render_template(request, "auth/login.html")


@auth_router.get("/register", name="auth.register_page")
async def register_page(request: Request):
    return render_template(request, "auth/register.html")


@auth_router.get("/password-reset", name="auth.password_reset_request_page")
async def password_reset_request_page(request: Request):
    return render_template(request, "auth/password_reset_request.html")


@auth_router.get("/verify-email", name="auth.verify_email_page")
async def verify_email_page(request: Request):
    return render_template(
        request,
        "auth/verify_email.html",
        email=_normalize_email(request.query_params.get("email")),
    )


@auth_router.get("/password-reset/confirm", name="auth.password_reset_confirm_page")
async def password_reset_confirm_page(request: Request):
    token = request.query_params.get("token", "")
    return render_template(
        request,
        "auth/password_reset_confirm.html",
        token=token,
    )


@auth_router.post("/login", name="auth.login_user")
@rate_limit(
    scope="auth_login",
    limit=Settings.auth_login_attempts_limit,
    window_seconds=Settings.auth_window_seconds,
    key_builder=lambda request: client_ip(request),
    response_mode="redirect",
    redirect_endpoint="auth.login_page",
)
async def login_user(request: Request):
    container = get_container(request)
    form = await request.form()
    email = _normalize_email(form.get("email"))
    password = form.get("password")
    if not email or len(email) > 254 or not password:
        flash(request, "Некорректные данные для входа")
        return RedirectResponse(
            url=request.app.url_path_for("auth.login_page"),
            status_code=303,
        )
    account_lock = getattr(container, "account_lock_service", None)
    if account_lock is not None:
        is_locked, _unlock_at = await account_lock.is_account_locked(email)
        if is_locked:
            logger.warning(
                "login_blocked_locked_account email=%s ip=%s",
                email, client_ip(request),
            )
            flash(request, "Аккаунт временно заблокирован из-за множества неудачных попыток входа. Попробуйте позже.")
            return RedirectResponse(
                url=request.app.url_path_for("auth.login_page"),
                status_code=303,
            )
    try:
        user = await container.login_user_use_case().execute(email=email, password=password)
        if account_lock is not None:
            await account_lock.unlock_account(email)
        logger.info("login_success user_id=%s ip=%s", user.id, client_ip(request))
        flash(request, f"Добро пожаловать, {user.username}!")
        response = RedirectResponse(
            url=request.app.url_path_for("index.index"),
            status_code=303,
        )
        _set_auth_cookies(response, user.id)
        return response
    except InvalidCredentialsError as error:
        if account_lock is not None:
            await account_lock.record_failed_attempt(email)
            status = await account_lock.get_account_status(email)
            logger.warning(
                "login_failed email=%s ip=%s attempts=%s/%s",
                email,
                client_ip(request),
                status.failed_attempts,
                status.max_attempts,
            )
        else:
            logger.warning("login_failed email=%s ip=%s", email, client_ip(request))
        flash(request, str(error))
        return RedirectResponse(
            url=request.app.url_path_for("auth.login_page"),
            status_code=303,
        )


@auth_router.post("/register", name="auth.register_user")
@rate_limit(
    scope="auth_register",
    limit=Settings.auth_register_attempts_limit,
    window_seconds=Settings.auth_window_seconds,
    key_builder=lambda request: client_ip(request),
    response_mode="redirect",
    redirect_endpoint="auth.register_page",
)
async def register_user(request: Request):
    container = get_container(request)
    form = await request.form()
    email = _normalize_email(form.get("email"))
    password = form.get("password")
    username = str(form.get("username") or "").strip()
    theme = _normalize_theme(form.get("theme"))
    if not email or len(email) > 254:
        flash(request, "Некорректный email")
        return RedirectResponse(
            url=request.app.url_path_for("auth.register_page"),
            status_code=303,
        )
    if not password or len(password) < 8 or len(password) > 128:
        flash(request, "Пароль должен быть не короче 8 символов")
        return RedirectResponse(
            url=request.app.url_path_for("auth.register_page"),
            status_code=303,
        )
    if not username or len(username) > 20:
        flash(request, "Некорректный username")
        return RedirectResponse(
            url=request.app.url_path_for("auth.register_page"),
            status_code=303,
        )
    try:
        await container.request_email_verification_use_case().execute(
            email=email,
            password=password,
            username=username,
            theme=theme,
        )
        logger.info("register_verification_requested email=%s ip=%s", email, client_ip(request))
        flash(request, "Мы отправили код подтверждения на почту. Введи его, чтобы завершить регистрацию.")
        return RedirectResponse(
            url=f"{request.app.url_path_for('auth.verify_email_page')}?email={email}",
            status_code=303,
        )
    except EmailAlreadyExistsError as error:
        flash(request, str(error))
    except RuntimeError as error:
        flash(request, str(error))
    return RedirectResponse(
        url=request.app.url_path_for("auth.register_page"),
        status_code=303,
    )


@auth_router.post("/verify-email", name="auth.verify_email")
@rate_limit(
    scope="auth_verify_email",
    limit=Settings.auth_verify_email_attempts_limit,
    window_seconds=Settings.auth_window_seconds,
    key_builder=lambda request: client_ip(request),
    response_mode="redirect",
    redirect_endpoint="auth.verify_email_page",
)
async def verify_email(request: Request):
    container = get_container(request)
    form = await request.form()
    email = _normalize_email(form.get("email"))
    code = _normalize_verification_code(form.get("code"))
    if not email or len(email) > 254:
        flash(request, "Некорректный email")
        return RedirectResponse(
            url=f"{request.app.url_path_for('auth.verify_email_page')}?email={email}",
            status_code=303,
        )
    if len(code) != 6:
        flash(request, "Код подтверждения должен содержать 6 цифр")
        return RedirectResponse(
            url=f"{request.app.url_path_for('auth.verify_email_page')}?email={email}",
            status_code=303,
        )
    try:
        user = await container.verify_email_use_case().execute(email=email, code=code)
        logger.info("email_verified user_id=%s ip=%s", user.id, client_ip(request))
        flash(request, f"Добро пожаловать, {user.username}!")
        response = RedirectResponse(
            url=request.app.url_path_for("index.index"),
            status_code=303,
        )
        _set_auth_cookies(response, user.id)
        return response
    except (
        InvalidEmailVerificationCodeError,
        EmailVerificationExpiredError,
        EmailAlreadyExistsError,
    ) as error:
        flash(request, str(error))
        return RedirectResponse(
            url=f"{request.app.url_path_for('auth.verify_email_page')}?email={email}",
            status_code=303,
        )


@auth_router.post("/verify-email/resend", name="auth.resend_verification_email")
@rate_limit(
    scope="auth_verify_email_resend",
    limit=Settings.auth_verify_email_resend_limit,
    window_seconds=Settings.auth_window_seconds,
    key_builder=lambda request: client_ip(request),
    response_mode="redirect",
    redirect_endpoint="auth.verify_email_page",
)
async def resend_verification_email(request: Request):
    container = get_container(request)
    form = await request.form()
    email = _normalize_email(form.get("email"))
    if not email or len(email) > 254:
        flash(request, "Некорректный email")
        return RedirectResponse(
            url=f"{request.app.url_path_for('auth.verify_email_page')}?email={email}",
            status_code=303,
        )
    try:
        await container.resend_email_verification_use_case().execute(email=email)
        flash(request, "Новый код подтверждения отправлен.")
    except (PendingEmailVerificationNotFoundError, RuntimeError) as error:
        flash(request, str(error))
    return RedirectResponse(
        url=f"{request.app.url_path_for('auth.verify_email_page')}?email={email}",
        status_code=303,
    )


@auth_router.post("/password-reset", name="auth.request_password_reset")
@rate_limit(
    scope="auth_password_reset",
    limit=Settings.auth_password_reset_attempts_limit,
    window_seconds=Settings.auth_window_seconds,
    key_builder=lambda request: client_ip(request),
    response_mode="redirect",
    redirect_endpoint="auth.password_reset_request_page",
)
async def request_password_reset(request: Request):
    container = get_container(request)
    form = await request.form()
    email = _normalize_email(form.get("email"))
    if not email or len(email) > 254:
        flash(request, "Некорректный email")
        return RedirectResponse(
            url=request.app.url_path_for("auth.password_reset_request_page"),
            status_code=303,
        )
    try:
        await container.request_password_reset_use_case().execute(
            email=email,
            base_url=str(request.base_url).rstrip("/"),
        )
        flash(request, "Если пользователь с таким email существует, мы отправили письмо со ссылкой для сброса пароля.")
    except RuntimeError as error:
        flash(request, str(error))
    return RedirectResponse(
        url=request.app.url_path_for("auth.password_reset_request_page"),
        status_code=303,
    )


@auth_router.post("/password-reset/confirm", name="auth.confirm_password_reset")
async def confirm_password_reset(request: Request):
    container = get_container(request)
    form = await request.form()
    token = str(form.get("token") or "").strip()
    password = str(form.get("password") or "")
    password_repeat = str(form.get("password_repeat") or "")

    if password != password_repeat:
        flash(request, "Пароли не совпадают")
        return RedirectResponse(
            url=f"{request.app.url_path_for('auth.password_reset_confirm_page')}?token={token}",
            status_code=303,
        )
    if len(password) < 8 or len(password) > 128:
        flash(request, "Пароль должен быть не короче 8 символов")
        return RedirectResponse(
            url=f"{request.app.url_path_for('auth.password_reset_confirm_page')}?token={token}",
            status_code=303,
        )

    try:
        await container.reset_password_use_case().execute(token=token, new_password=password)
        flash(request, "Пароль обновлен. Теперь можно войти.")
        return RedirectResponse(
            url=request.app.url_path_for("auth.login_page"),
            status_code=303,
        )
    except InvalidPasswordResetTokenError as error:
        flash(request, str(error))
        return RedirectResponse(
            url=f"{request.app.url_path_for('auth.password_reset_confirm_page')}?token={token}",
            status_code=303,
        )


@auth_router.post("/logout", name="auth.logout_user")
async def logout_user(request: Request):
    container = get_container(request)
    await _revoke_auth_tokens_from_request(request, container)
    response = RedirectResponse(
        url=request.app.url_path_for("index.index"),
        status_code=303,
    )
    _clear_auth_cookies(response)
    return response


@auth_router.post("/refresh", name="auth.refresh_session")
@rate_limit(
    scope="auth_refresh",
    limit=10,
    window_seconds=Settings.auth_window_seconds,
    key_builder=lambda request: client_ip(request),
)
async def refresh_session(request: Request):
    container = get_container(request)
    refresh_token = str(request.cookies.get("refresh_token") or "").strip()
    token_blocklist = getattr(container, "token_blocklist", None)
    if not refresh_token:
        return JSONResponse({"error": "auth_required"}, status_code=401)
    if token_blocklist is not None and await token_blocklist.is_revoked(refresh_token):
        return JSONResponse({"error": "invalid_token"}, status_code=401)
    try:
        user_id = jwt_service.decode_refresh_token(refresh_token)
    except Exception:
        logger.warning("refresh_failed ip=%s", client_ip(request), exc_info=True)
        return JSONResponse({"error": "invalid_token"}, status_code=401)

    if token_blocklist is not None:
        await token_blocklist.revoke(
            refresh_token,
            jwt_service.get_token_ttl_seconds(refresh_token, expected_type="refresh"),
        )

    response = JSONResponse({"status": "ok"})
    _set_auth_cookies(response, user_id)
    return response


@auth_router.get("/profile", name="auth.profile_page")
async def profile_page(request: Request):
    container = get_container(request)
    user = get_current_user(request)
    if not user:
        return RedirectResponse(
            url=request.app.url_path_for("auth.login_page"),
            status_code=303,
        )
    overview = await container.get_profile_overview_use_case().execute(user.id)
    return render_template(
        request,
        "auth/profile.html",
        profile_user=user,
        profile_overview=overview,
    )


@auth_router.post("/profile", name="auth.update_profile")
async def update_profile(request: Request):
    container = get_container(request)
    user = get_current_user(request)
    if not user:
        return RedirectResponse(
            url=request.app.url_path_for("auth.login_page"),
            status_code=303,
        )
    form = await request.form()
    username = form.get("username", "")
    avatar_url = form.get("avatar_url")

    try:
        await container.update_user_profile_use_case().execute(
            user_id=user.id,
            username=username,
            avatar_url=avatar_url,
        )
        flash(request, "Профиль обновлён")
    except (InvalidProfileDataError, UserNotFoundError) as error:
        flash(request, str(error))

    return RedirectResponse(
        url=request.app.url_path_for("auth.profile_page"),
        status_code=303,
    )


def _normalize_email(value: str | None) -> str:
    return str(value or "").strip().lower()


def _normalize_verification_code(value: str | None) -> str:
    return "".join(character for character in str(value or "") if character.isdigit())


def _normalize_theme(value: str | None) -> str:
    normalized = str(value or "").strip().lower()
    return normalized if normalized in {"neon", "dark", "light", "rose"} else "neon"


def _set_auth_cookies(response, user_id: int):
    access_token = jwt_service.create_access_token(user_id)
    refresh_token = jwt_service.create_refresh_token(user_id)
    cookie_kwargs = {
        "httponly": True,
        "secure": Settings.cookie_secure,
        "samesite": Settings.cookie_samesite,
        "path": "/",
    }
    if Settings.cookie_domain:
        cookie_kwargs["domain"] = Settings.cookie_domain
    response.set_cookie(
        "access_token",
        access_token,
        max_age=Settings.access_token_expire_minutes * 60,
        **cookie_kwargs,
    )
    response.set_cookie(
        "refresh_token",
        refresh_token,
        max_age=Settings.refresh_token_expire_days * 24 * 60 * 60,
        **cookie_kwargs,
    )


def _clear_auth_cookies(response):
    cookie_kwargs = {
        "httponly": True,
        "secure": Settings.cookie_secure,
        "samesite": Settings.cookie_samesite,
        "path": "/",
    }
    if Settings.cookie_domain:
        cookie_kwargs["domain"] = Settings.cookie_domain
    response.delete_cookie("access_token", **cookie_kwargs)
    response.delete_cookie("refresh_token", **cookie_kwargs)


async def _revoke_auth_tokens_from_request(request: Request, container):
    token_blocklist = getattr(container, "token_blocklist", None)
    if token_blocklist is None:
        return
    for cookie_name, expected_type in (
        ("access_token", "access"),
        ("refresh_token", "refresh"),
    ):
        token = str(request.cookies.get(cookie_name) or "").strip()
        if not token:
            continue
        try:
            await token_blocklist.revoke(
                token,
                jwt_service.get_token_ttl_seconds(token, expected_type=expected_type),
            )
        except Exception:
            logger.warning(
                "token_revoke_failed cookie=%s ip=%s",
                cookie_name,
                client_ip(request),
                exc_info=True,
            )
