from flask import (
    Blueprint,
    current_app,
    jsonify,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    make_response,
    g,
)
from src.backend.dependencies.settings import Settings
from src.backend.dependencies.container import container
from src.backend.infrastructure.security.flask_protection import (
    client_ip,
    rate_limit,
)
from src.backend.infrastructure.security.jwt_service import JWTService
from src.backend.use_case.auth.login_user import InvalidCredentialsError
from src.backend.use_case.auth.register_user import EmailAlreadyExistsError
from src.backend.use_case.auth.reset_password import InvalidPasswordResetTokenError
from src.backend.use_case.auth.update_user_profile import (
    InvalidProfileDataError,
    UserNotFoundError,
)

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

jwt_service = JWTService()
LOGIN_ATTEMPTS_LIMIT = 5
REGISTER_ATTEMPTS_LIMIT = 3
PASSWORD_RESET_ATTEMPTS_LIMIT = 3
AUTH_WINDOW_SECONDS = 300


@auth_bp.route("/login", methods=["GET"])
def login_page():
    """Рендер страницы входа"""
    return render_template("auth/login.html")


@auth_bp.route("/register", methods=["GET"])
def register_page():
    """Рендер страницы регистрации"""
    return render_template("auth/register.html")


@auth_bp.route("/password-reset", methods=["GET"])
def password_reset_request_page():
    """Рендер страницы запроса сброса пароля."""
    return render_template("auth/password_reset_request.html")


@auth_bp.route("/password-reset/confirm", methods=["GET"])
def password_reset_confirm_page():
    """Рендер страницы установки нового пароля по токену."""
    token = request.args.get("token", "")
    return render_template("auth/password_reset_confirm.html", token=token)


@auth_bp.route("/login", methods=["POST"])
@rate_limit(
    container_getter=lambda: container,
    scope="auth_login",
    limit=LOGIN_ATTEMPTS_LIMIT,
    window_seconds=AUTH_WINDOW_SECONDS,
    key_builder=lambda: _auth_attempt_subject(request.form.get("email")),
    response_mode="redirect",
    redirect_endpoint="auth.login_page",
)
def login_user():
    """Обработка входа пользователя"""
    email = _normalize_email(request.form.get("email"))
    password = request.form.get("password")
    if not email or len(email) > 254 or not password:
        flash("Некорректные данные для входа")
        return redirect(url_for("auth.login_page"))
    try:
        user = container.login_user_use_case().execute(email=email, password=password)
        current_app.logger.info("login_success user_id=%s ip=%s", user.id, client_ip())
        flash(f"Добро пожаловать, {user.username}!")
        resp = make_response(redirect(url_for("index.index")))
        _set_auth_cookies(resp, user.id)
        return resp
    except InvalidCredentialsError as e:
        current_app.logger.warning(
            "login_failed email=%s ip=%s",
            email,
            client_ip(),
        )
        flash(str(e))
        return redirect(url_for("auth.login_page"))


@auth_bp.route("/register", methods=["POST"])
@rate_limit(
    container_getter=lambda: container,
    scope="auth_register",
    limit=REGISTER_ATTEMPTS_LIMIT,
    window_seconds=AUTH_WINDOW_SECONDS,
    key_builder=lambda: _auth_attempt_subject(request.form.get("email")),
    response_mode="redirect",
    redirect_endpoint="auth.register_page",
)
def register_user():
    """Обработка регистрации пользователя"""
    email = _normalize_email(request.form.get("email"))
    password = request.form.get("password")
    username = str(request.form.get("username") or "").strip()
    if not email or len(email) > 254:
        flash("Некорректный email")
        return redirect(url_for("auth.register_page"))
    if not password or len(password) < 8 or len(password) > 128:
        flash("Пароль должен быть не короче 8 символов")
        return redirect(url_for("auth.register_page"))
    if not username or len(username) > 20:
        flash("Некорректный username")
        return redirect(url_for("auth.register_page"))
    try:
        user = container.register_user_use_case().execute(
            email=email, password=password, username=username
        )
        current_app.logger.info(
            "register_success user_id=%s ip=%s",
            user.id,
            client_ip(),
        )
        flash(f"Добро пожаловать, {user.username}!")
        resp = make_response(redirect(url_for("index.index")))
        _set_auth_cookies(resp, user.id)
        return resp
    except EmailAlreadyExistsError as e:
        flash(str(e))
        return redirect(url_for("auth.register_page"))


@auth_bp.route("/password-reset", methods=["POST"])
@rate_limit(
    container_getter=lambda: container,
    scope="auth_password_reset",
    limit=PASSWORD_RESET_ATTEMPTS_LIMIT,
    window_seconds=AUTH_WINDOW_SECONDS,
    key_builder=lambda: _auth_attempt_subject(request.form.get("email")),
    response_mode="redirect",
    redirect_endpoint="auth.password_reset_request_page",
)
def request_password_reset():
    """Обрабатывает запрос на сброс пароля и отправляет письмо."""
    email = _normalize_email(request.form.get("email", ""))
    if not email or len(email) > 254:
        flash("Некорректный email")
        return redirect(url_for("auth.password_reset_request_page"))
    try:
        container.request_password_reset_use_case().execute(
            email=email, base_url=request.url_root.rstrip("/")
        )
        flash(
            "Если пользователь с таким email существует, мы отправили письмо со ссылкой для сброса пароля."
        )
    except RuntimeError as error:
        flash(str(error))
    return redirect(url_for("auth.password_reset_request_page"))


@auth_bp.route("/password-reset/confirm", methods=["POST"])
def confirm_password_reset():
    """Сохраняет новый пароль пользователя по reset token."""
    token = request.form.get("token", "").strip()
    password = request.form.get("password", "")
    password_repeat = request.form.get("password_repeat", "")

    if password != password_repeat:
        flash("Пароли не совпадают")
        return redirect(url_for("auth.password_reset_confirm_page", token=token))
    if len(password) < 8 or len(password) > 128:
        flash("Пароль должен быть не короче 8 символов")
        return redirect(url_for("auth.password_reset_confirm_page", token=token))

    try:
        container.reset_password_use_case().execute(token=token, new_password=password)
        flash("Пароль обновлен. Теперь можно войти.")
        return redirect(url_for("auth.login_page"))
    except InvalidPasswordResetTokenError as error:
        flash(str(error))
        return redirect(url_for("auth.password_reset_confirm_page", token=token))


@auth_bp.route("/logout", methods=["POST"])
def logout_user():
    """Обработка выхода пользователя"""
    _revoke_auth_tokens_from_request()
    resp = make_response(redirect(url_for("index.index")))
    _clear_auth_cookies(resp)
    return resp


@auth_bp.route("/refresh", methods=["POST"])
@rate_limit(
    container_getter=lambda: container,
    scope="auth_refresh",
    limit=10,
    window_seconds=AUTH_WINDOW_SECONDS,
    key_builder=lambda: client_ip(),
)
def refresh_session():
    """Перевыпускает access и refresh token по валидному refresh token."""
    refresh_token = str(request.cookies.get("refresh_token") or "").strip()
    token_blocklist = getattr(container, "token_blocklist", None)
    if not refresh_token:
        return jsonify({"error": "auth_required"}), 401
    if token_blocklist is not None and token_blocklist.is_revoked(refresh_token):
        return jsonify({"error": "invalid_token"}), 401
    try:
        user_id = jwt_service.decode_refresh_token(refresh_token)
    except Exception:
        current_app.logger.warning("refresh_failed ip=%s", client_ip(), exc_info=True)
        return jsonify({"error": "invalid_token"}), 401

    if token_blocklist is not None:
        token_blocklist.revoke(
            refresh_token,
            jwt_service.get_token_ttl_seconds(refresh_token, expected_type="refresh"),
        )

    response = jsonify({"status": "ok"})
    _set_auth_cookies(response, user_id)
    return response


@auth_bp.route("/profile", methods=["GET"])
def profile_page():
    """Рендер страницы профиля текущего пользователя."""
    user = getattr(g, "user", None)
    if not user:
        return redirect(url_for("auth.login_page"))
    return render_template("auth/profile.html", profile_user=user)


@auth_bp.route("/profile", methods=["POST"])
def update_profile():
    """Обновляет профиль текущего пользователя."""
    user = getattr(g, "user", None)
    if not user:
        return redirect(url_for("auth.login_page"))

    username = request.form.get("username", "")
    avatar_url = request.form.get("avatar_url")

    try:
        container.update_user_profile_use_case().execute(
            user_id=user.id, username=username, avatar_url=avatar_url
        )
        flash("Профиль обновлён")
    except (InvalidProfileDataError, UserNotFoundError) as error:
        flash(str(error))

    return redirect(url_for("auth.profile_page"))


def _normalize_email(value: str | None) -> str:
    return str(value or "").strip().lower()


def _auth_attempt_subject(email: str | None) -> str:
    normalized_email = _normalize_email(email) or "anonymous"
    return f"{client_ip()}::{normalized_email}"


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
    response.set_cookie("access_token", "", expires=0, **cookie_kwargs)
    response.set_cookie("refresh_token", "", expires=0, **cookie_kwargs)


def _revoke_auth_tokens_from_request():
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
            token_blocklist.revoke(
                token,
                jwt_service.get_token_ttl_seconds(token, expected_type=expected_type),
            )
        except Exception:
            current_app.logger.warning(
                "token_revoke_failed cookie=%s ip=%s",
                cookie_name,
                client_ip(),
                exc_info=True,
            )
