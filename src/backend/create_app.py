from pathlib import Path

from flask import Flask, g, request, render_template, jsonify

from src.backend.delivery.api.v1.index_route import index_bp
from src.backend.dependencies.settings import Settings
from src.backend.delivery.api.v1.auth_route import auth_bp
from src.backend.delivery.api.v1.highlight_route import highlight_bp
from src.backend.delivery.api.v1.favorite_route import favorite_bp
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

    if Settings.database_auto_init:
        init_db()

    jwt_service = JWTService()

    @app.before_request
    def load_user():
        """Загружает пользователя из access_token в g."""
        token = request.cookies.get("access_token")
        if token:
            try:
                user_id = jwt_service.decode_token(token)
                from src.backend.dependencies.container import container

                user = container.user_repository.get_by_id(user_id)
                g.user = user
            except:
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

    app.register_blueprint(auth_bp)
    app.register_blueprint(highlight_bp)
    app.register_blueprint(favorite_bp)
    app.register_blueprint(anime_bp)
    app.register_blueprint(watch_bp)
    app.register_blueprint(recommendation_bp)
    app.register_blueprint(index_bp)

    return app
