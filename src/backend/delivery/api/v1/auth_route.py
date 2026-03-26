from flask import Blueprint, render_template, request, redirect, url_for, flash, make_response, g
from src.backend.dependencies.container import container
from src.backend.infrastructure.security.jwt_service import JWTService
from src.backend.use_case.auth.login_user import InvalidCredentialsError
from src.backend.use_case.auth.register_user import EmailAlreadyExistsError
from src.backend.use_case.auth.reset_password import InvalidPasswordResetTokenError
from src.backend.use_case.auth.update_user_profile import InvalidProfileDataError, UserNotFoundError

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

jwt_service = JWTService()

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
def login_user():
    """Обработка входа пользователя"""
    email = request.form.get("email")
    password = request.form.get("password")
    try:
        user = container.login_user_use_case().execute(email=email, password=password)
        token = jwt_service.create_token(user.id)
        flash(f"Добро пожаловать, {user.username}!")
        resp = make_response(redirect(url_for("index.index")))
        resp.set_cookie("access_token", token, httponly=True, max_age=60*60*24)
        return resp
    except InvalidCredentialsError as e:
        flash(str(e))
        return redirect(url_for("auth.login_page"))

@auth_bp.route("/register", methods=["POST"])
def register_user():
    """Обработка регистрации пользователя"""
    email = request.form.get("email")
    password = request.form.get("password")
    username = request.form.get("username")
    if not password or len(password) < 8:
        flash("Пароль должен быть не короче 8 символов")
        return redirect(url_for("auth.register_page"))
    try:
        user = container.register_user_use_case().execute(
            email=email, password=password, username=username
        )
        token = jwt_service.create_token(user.id)
        flash(f"Добро пожаловать, {user.username}!")
        resp = make_response(redirect(url_for("index.index")))
        resp.set_cookie("access_token", token, httponly=True, max_age=60*60*24)
        return resp
    except EmailAlreadyExistsError as e:
        flash(str(e))
        return redirect(url_for("auth.register_page"))


@auth_bp.route("/password-reset", methods=["POST"])
def request_password_reset():
    """Обрабатывает запрос на сброс пароля и отправляет письмо."""
    email = request.form.get("email", "").strip()
    try:
        container.request_password_reset_use_case().execute(
            email=email,
            base_url=request.url_root.rstrip("/")
        )
        flash("Если пользователь с таким email существует, мы отправили письмо со ссылкой для сброса пароля.")
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
    if len(password) < 8:
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
    resp = make_response(redirect(url_for("index.index")))
    resp.set_cookie("access_token", "", expires=0)
    return resp

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
            user_id=user.id,
            username=username,
            avatar_url=avatar_url
        )
        flash("Профиль обновлён")
    except (InvalidProfileDataError, UserNotFoundError) as error:
        flash(str(error))

    return redirect(url_for("auth.profile_page"))
