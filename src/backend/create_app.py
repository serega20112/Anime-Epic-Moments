from pathlib import Path
from urllib.parse import urlparse

import jwt
from flask import Flask, current_app, g, request, render_template, jsonify

from src.backend.delivery.api.v1.index_route import index_bp
from src.backend.dependencies.settings import Settings
from src.backend.delivery.api.v1.auth_route import auth_bp
from src.backend.delivery.api.v1.highlight_route import highlight_bp
from src.backend.delivery.api.v1.favorite_route import favorite_bp
from src.backend.delivery.api.v1.collection_route import collection_bp
from src.backend.delivery.api.v1.anime_route import anime_bp
from src.backend.delivery.api.v1.recommendation_route import recommendation_bp
from src.backend.delivery.api.v1.watch_route import watch_bp
from src.backend.infrastructure.security.jwt_service import JWTService
from src.backend.infrastructure.files.database import init_db

PROJECT_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_ROOT = PROJECT_ROOT / "src" / "frontend"


def create_app():
    """Создаёт Flask приложение, подключает роуты"""
    app = Flask(
        __name__,
        static_folder=str(FRONTEND_ROOT / "static"),
        template_folder=str(FRONTEND_ROOT / "templates"),
    )
    app.config["SECRET_KEY"] = Settings.secret_key
    app.config["MAX_CONTENT_LENGTH"] = Settings.max_request_bytes

    if Settings.database_auto_init:
        init_db()

    jwt_service = JWTService()

    @app.before_request
    def load_user():
        """Загружает пользователя из access_token в g."""
        if _is_static_request():
            g.user = None
            return

        if _is_cross_origin_write_request():
            current_app.logger.warning(
                "cross_origin_write_blocked path=%s origin=%s referer=%s",
                request.path,
                request.headers.get("Origin"),
                request.headers.get("Referer"),
            )
            return jsonify({"error": "forbidden_origin"}), 403

        token = request.cookies.get("access_token")
        if token:
            try:
                from src.backend.dependencies.container import container

                token_blocklist = getattr(container, "token_blocklist", None)
                if token_blocklist is not None and token_blocklist.is_revoked(token):
                    current_app.logger.info(
                        "revoked_access_token_used path=%s",
                        request.path,
                    )
                    g.clear_access_token_cookie = True
                    g.user = None
                    return
                user_id = jwt_service.decode_token(token)
                user = container.user_repository.get_by_id(user_id)
                g.user = user
            except jwt.InvalidTokenError as error:
                current_app.logger.info(
                    "access_token_rejected reason=%s path=%s",
                    error.__class__.__name__,
                    request.path,
                )
                g.clear_access_token_cookie = True
                g.user = None
            except Exception:
                current_app.logger.warning(
                    "access_token_decode_failed path=%s",
                    request.path,
                    exc_info=True,
                )
                g.user = None
        else:
            g.user = None

    @app.context_processor
    def inject_current_user():
        """Прокидывает текущего пользователя в шаблоны."""
        return {"current_user": getattr(g, "user", None)}

    @app.errorhandler(500)
    def handle_internal_error(_error):
        """Возвращает аккуратный ответ на внутренние ошибки сервера."""
        wants_json = (
            request.is_json or request.accept_mimetypes.best == "application/json"
        )
        if wants_json:
            return jsonify({"error": "internal_server_error"}), 500
        return render_template("errors/500_modal.html"), 500

    @app.errorhandler(413)
    def handle_request_too_large(_error):
        """Возвращает аккуратный ответ на слишком большой payload."""
        current_app.logger.warning("request_too_large path=%s", request.path)
        wants_json = (
            request.is_json or request.accept_mimetypes.best == "application/json"
        )
        if wants_json:
            return jsonify({"error": "request_too_large"}), 413
        return "Payload too large", 413

    @app.after_request
    def apply_security_headers(response):
        """Добавляет базовые security headers к каждому ответу."""
        if getattr(g, "clear_access_token_cookie", False):
            _clear_cookie(response, "access_token")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("Referrer-Policy", "same-origin")
        response.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'self'; "
            "img-src 'self' data: https: blob:; "
            "style-src 'self' 'unsafe-inline' https:; "
            "style-src-elem 'self' 'unsafe-inline' https:; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "connect-src 'self' https:; "
            "media-src 'self' https: blob:; "
            "worker-src 'self' blob:; "
            "frame-src 'self' https:; "
            "font-src 'self' data: https:; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'",
        )
        return response

    app.register_blueprint(auth_bp)
    app.register_blueprint(highlight_bp)
    app.register_blueprint(favorite_bp)
    app.register_blueprint(collection_bp)
    app.register_blueprint(anime_bp)
    app.register_blueprint(watch_bp)
    app.register_blueprint(recommendation_bp)
    app.register_blueprint(index_bp)

    return app


def _is_cross_origin_write_request() -> bool:
    if request.method not in {"POST", "PUT", "PATCH", "DELETE"}:
        return False
    source = _extract_request_origin()
    if not source:
        return False
    return source not in _get_allowed_origins()


def _extract_request_origin() -> str | None:
    source = request.headers.get("Origin") or request.headers.get("Referer")
    if not source:
        return None
    parsed = urlparse(str(source).strip())
    if not parsed.scheme or not parsed.netloc:
        return None
    return f"{parsed.scheme}://{parsed.netloc}".rstrip("/")


def _normalize_origin(value: str | None) -> str | None:
    parsed = urlparse(str(value or "").strip())
    if not parsed.scheme or not parsed.netloc:
        return None
    return f"{parsed.scheme}://{parsed.netloc}".rstrip("/")


def _get_allowed_origins() -> set[str]:
    allowed = {
        origin
        for origin in (
            _normalize_origin(request.host_url),
            _normalize_origin(Settings.app_base_url),
            *(_normalize_origin(item) for item in Settings.app_allowed_origins),
        )
        if origin
    }
    return allowed


def _is_static_request() -> bool:
    return request.endpoint == "static" or request.path.startswith("/static/")


def _clear_cookie(response, cookie_name: str):
    cookie_kwargs = {
        "httponly": True,
        "secure": Settings.cookie_secure,
        "samesite": Settings.cookie_samesite,
        "path": "/",
    }
    if Settings.cookie_domain:
        cookie_kwargs["domain"] = Settings.cookie_domain
    response.set_cookie(cookie_name, "", expires=0, **cookie_kwargs)
