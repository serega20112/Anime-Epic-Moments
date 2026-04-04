from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
from flask import Flask, g
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture
def anime_factory():
    """Создает сущности Anime с переопределяемыми полями для тестов."""
    from src.backend.domain.anime.entity import Anime

    def _build(**overrides):
        payload = {
            "external_id": "101",
            "title": "Test Anime",
            "description": "Test description",
            "genres": ["Action", "Comedy"],
            "year": 2024,
            "rating": 8.4,
            "cover_url": "https://example.com/cover.jpg",
            "episode_count": 12,
        }
        payload.update(overrides)
        return Anime(**payload)

    return _build


@pytest.fixture
def flask_app_factory():
    """Создает Flask app для тестирования отдельных blueprint'ов."""

    def _build(*blueprints, user=None):
        app = Flask(
            __name__,
            template_folder=str(PROJECT_ROOT / "src" / "frontend" / "templates"),
            static_folder=str(PROJECT_ROOT / "src" / "frontend" / "static"),
        )
        app.config.update(TESTING=True, SECRET_KEY="test-secret")

        @app.before_request
        def _load_user():
            g.user = user

        @app.context_processor
        def _inject_current_user():
            return {"current_user": user}

        for blueprint in blueprints:
            app.register_blueprint(blueprint)

        def _register_placeholder(rule, endpoint, methods=("GET",)):
            if endpoint in app.view_functions:
                return

            def _placeholder(**kwargs):
                return ""

            app.add_url_rule(rule, endpoint=endpoint, view_func=_placeholder, methods=list(methods))

        _register_placeholder("/anime/search", "anime.search_anime_page")
        _register_placeholder("/anime/search/description", "anime.search_by_description_page")
        _register_placeholder("/highlights/<int:user_id>", "highlight.get_user_highlights")
        _register_placeholder("/highlights/top", "highlight.get_public_top_highlights")
        _register_placeholder("/highlights/feed", "highlight.get_highlight_feed")
        _register_placeholder("/highlights/following", "highlight.get_following_highlights")
        _register_placeholder("/highlights/saved", "highlight.get_saved_highlights")
        _register_placeholder("/highlights/liked", "highlight.get_liked_highlights")
        _register_placeholder("/highlights/notifications", "highlight.get_highlight_notifications")
        _register_placeholder("/favorites/<int:user_id>", "favorite.get_favorites")
        _register_placeholder("/collections", "collection.collections_page")
        _register_placeholder("/collections/share/<int:collection_id>", "collection.shared_collection_page")
        _register_placeholder("/auth/profile", "auth.profile_page")
        _register_placeholder("/auth/login", "auth.login_page")
        _register_placeholder("/auth/register", "auth.register_page")
        _register_placeholder("/auth/logout", "auth.logout_user", methods=("POST",))
        _register_placeholder("/support", "support.support_page")
        _register_placeholder("/users/<int:user_id>", "user.public_profile_page")
        _register_placeholder("/users/<int:user_id>/follow", "user.follow_user", methods=("POST",))
        _register_placeholder("/users/<int:user_id>/unfollow", "user.unfollow_user", methods=("POST",))
        _register_placeholder("/watch/<int:anime_id>", "watch.watch_page")
        _register_placeholder("/", "index.index")
        return app

    return _build


@pytest.fixture
def user_factory():
    """Создает простого пользователя для тестов роутов и use case."""

    def _build(**overrides):
        payload = {
            "id": 1,
            "email": "user@example.com",
            "username": "tester",
            "avatar_url": None,
        }
        payload.update(overrides)
        return SimpleNamespace(**payload)

    return _build


@pytest.fixture
def db_session():
    """Создает изолированную SQLAlchemy-сессию в памяти для repository-тестов."""
    from src.backend.infrastructure.files.database import Base

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()
