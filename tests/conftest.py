from __future__ import annotations

import asyncio
import functools
import importlib
import inspect
import re
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, NonCallableMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.middleware.sessions import SessionMiddleware
from starlette.staticfiles import StaticFiles

PROJECT_ROOT = Path(__file__).resolve().parents[3]
FRONTEND_ROOT = PROJECT_ROOT / "src" / "frontend"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

_ASYNC_COMPAT_METHOD_NAMES = {
    "add",
    "add_source",
    "add_translation",
    "autocomplete_anime",
    "build_search_queries_with_meta",
    "contains",
    "delete",
    "delete_prefix",
    "describe_taste_profile",
    "execute",
    "get",
    "get_ai_summary",
    "get_anime_discussion",
    "get_by_anime_episode",
    "get_by_email",
    "get_by_id",
    "get_by_ids",
    "get_by_user",
    "get_by_users",
    "get_enabled_provider_names",
    "get_engagement_map",
    "get_follow_stats",
    "get_followed_user_ids",
    "get_followed_users",
    "get_highlight_contexts",
    "get_liked_by_user",
    "get_overview",
    "get_profile_summary",
    "get_provider_label",
    "get_public",
    "get_public_recent",
    "get_public_top",
    "get_recent_activity",
    "get_saved_by_user",
    "get_season_popular",
    "get_session",
    "get_sources",
    "get_status",
    "get_top_anime",
    "get_translations",
    "get_ttl",
    "get_viewing_heatmap",
    "get_watched_anime_stats",
    "hit",
    "increment",
    "invalidate_overview",
    "invalidate_public",
    "invalidate_user",
    "is_revoked",
    "is_enabled",
    "revoke",
    "save",
    "search_by_description",
    "search_by_title",
    "search_sources",
    "set",
    "set_ai_summary",
    "set_overview",
    "set_public",
    "sync_for_anime",
    "update",
}
_ASYNC_COMPAT_INSTANCE_HELPERS = {
    "_build_dashboard",
    "_build_taste_summary",
    "_load_anime_map",
    "_load_owner_map",
}
_HYBRID_MODULE_PREFIXES = (
    "backend.application.use_cases.",
    "backend.application.services.",
    "backend.infrastructure.repositories.",
    "backend.infrastructure.cache.",
    "backend.infrastructure.security.",
    "backend.infrastructure.external.",
    "backend.infrastructure.files.",
)


def _collect_async_method_names():
    async_method_pattern = re.compile(r"async def\s+([A-Za-z_][A-Za-z0-9_]*)")
    source_roots = (
        PROJECT_ROOT / "src" / "backend" / "use_case",
        PROJECT_ROOT / "src" / "backend" / "services",
        PROJECT_ROOT / "src" / "backend" / "infrastructure" / "repositories",
        PROJECT_ROOT / "src" / "backend" / "infrastructure" / "cache",
        PROJECT_ROOT / "src" / "backend" / "infrastructure" / "security",
        PROJECT_ROOT / "src" / "backend" / "infrastructure" / "external",
        PROJECT_ROOT / "src" / "backend" / "infrastructure" / "files",
    )
    names = set(_ASYNC_COMPAT_METHOD_NAMES)
    for root in source_roots:
        if not root.exists():
            continue
        for path in root.rglob("*.py"):
            try:
                names.update(async_method_pattern.findall(path.read_text(encoding="utf-8")))
            except OSError:
                continue
    return names


_ASYNC_COMPAT_METHOD_NAMES = _collect_async_method_names()


class CompatHeaders:
    def __init__(self, headers):
        self._headers = headers

    def __contains__(self, item):
        return item in self._headers

    def __getitem__(self, item):
        return self._headers[item]

    def get(self, key, default=None):
        return self._headers.get(key, default)

    def getlist(self, key):
        return list(self._headers.get_list(key))


class CompatResponse:
    def __init__(self, response):
        self._response = response
        self.headers = CompatHeaders(response.headers)

    @property
    def status_code(self):
        return self._response.status_code

    @property
    def text(self):
        return self._response.text

    def get_json(self):
        try:
            return self._response.json()
        except Exception:
            return None

    def get_data(self, as_text=False):
        return self._response.text if as_text else self._response.content


class CompatClient:
    def __init__(self, app):
        self._client = TestClient(app)

    def close(self):
        self._client.close()

    def set_cookie(self, key, value, domain="testserver", path="/"):
        self._client.cookies.set(key, value, domain=domain, path=path)

    def request(self, method, path, base_url=None, **kwargs):
        url = str(path)
        if base_url:
            url = f"{str(base_url).rstrip('/')}{url}"
        kwargs.setdefault("follow_redirects", False)
        return CompatResponse(self._client.request(method, url, **kwargs))

    def get(self, path, **kwargs):
        return self.request("GET", path, **kwargs)

    def post(self, path, **kwargs):
        return self.request("POST", path, **kwargs)

    def put(self, path, **kwargs):
        return self.request("PUT", path, **kwargs)

    def delete(self, path, **kwargs):
        return self.request("DELETE", path, **kwargs)

    def head(self, path, **kwargs):
        return self.request("HEAD", path, **kwargs)


class CompatApp:
    def __init__(self, app: FastAPI):
        self.app = app

    def test_client(self):
        return CompatClient(self.app)


class AsyncCompatProxy:
    def __init__(self, value):
        self._value = value

    def __getattr__(self, name):
        attr = getattr(self._value, name)
        if callable(attr):
            if name.endswith("_use_case"):

                @functools.wraps(attr)
                def factory(*args, **kwargs):
                    return AsyncCompatProxy(attr(*args, **kwargs))

                return factory
            if name in _ASYNC_COMPAT_METHOD_NAMES:

                @functools.wraps(attr)
                async def awaited(*args, **kwargs):
                    result = attr(*args, **kwargs)
                    if inspect.isawaitable(result):
                        return await result
                    return result

                return awaited
            return attr
        if _should_wrap_value(attr):
            return AsyncCompatProxy(attr)
        return attr


def _should_wrap_value(value) -> bool:
    if inspect.isfunction(value) or inspect.ismethod(value) or inspect.isbuiltin(value):
        return False
    if isinstance(
        value, (AsyncCompatProxy, str, bytes, int, float, bool, list, tuple, dict, set, type(None))
    ):
        return False
    if isinstance(value, (SimpleNamespace, Mock, NonCallableMock)):
        return True
    module_name = type(value).__module__
    return module_name.startswith("tests.") or module_name.startswith("backend.tests.")


def _wrap_test_container(value):
    if value is None:
        return SimpleNamespace()
    if isinstance(value, AsyncCompatProxy):
        return value
    if not _should_wrap_value(value):
        return value
    return AsyncCompatProxy(value)


def _patch_async_callable(async_callable):
    if not inspect.iscoroutinefunction(async_callable):
        return None
    if getattr(async_callable, "__sync_compat_wrapped__", False):
        return None

    @functools.wraps(async_callable)
    def wrapped(*args, **kwargs):
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            if args and hasattr(args[0], "__dict__"):
                for attr_name, attr_value in list(vars(args[0]).items()):
                    if callable(attr_value) and attr_name in _ASYNC_COMPAT_INSTANCE_HELPERS:

                        async def _wrapped_helper(*helper_args, __attr=attr_value, **helper_kwargs):
                            result = __attr(*helper_args, **helper_kwargs)
                            if inspect.isawaitable(result):
                                return await result
                            return result

                        setattr(args[0], attr_name, _wrapped_helper)
                        continue
                    if _should_wrap_value(attr_value):
                        setattr(args[0], attr_name, _wrap_test_container(attr_value))
            coroutine = async_callable(*args, **kwargs)
            return asyncio.run(coroutine)
        coroutine = async_callable(*args, **kwargs)
        return coroutine

    wrapped.__sync_compat_wrapped__ = True
    return wrapped


def _patch_async_methods_for_sync_tests():
    for module_name, module in list(sys.modules.items()):
        if not any(module_name.startswith(prefix) for prefix in _HYBRID_MODULE_PREFIXES):
            continue
        if module is None:
            continue
        for attr_name, attr_value in list(vars(module).items()):
            if (
                inspect.isclass(attr_value)
                and getattr(attr_value, "__module__", None) == module_name
            ):
                for method_name, method_value in list(vars(attr_value).items()):
                    patched = _patch_async_callable(method_value)
                    if patched is not None:
                        setattr(attr_value, method_name, patched)
                continue
            patched = _patch_async_callable(attr_value)
            if patched is not None:
                setattr(module, attr_name, patched)


def pytest_collection_modifyitems(session, config, items):
    _patch_async_methods_for_sync_tests()


def _install_fastapi_test_compat():
    if not hasattr(FastAPI, "test_client"):
        FastAPI.test_client = lambda self: CompatClient(self)
    if not hasattr(FastAPI, "route"):

        def route(self, path, methods=("GET",)):
            normalized_methods = list(methods or ("GET",))

            def decorator(handler):
                if inspect.iscoroutinefunction(handler):
                    endpoint = handler
                else:

                    @functools.wraps(handler)
                    async def endpoint(*args, **kwargs):
                        return handler(*args, **kwargs)

                self.add_api_route(
                    path, endpoint, methods=normalized_methods, name=handler.__name__
                )
                return handler

            return decorator

        FastAPI.route = route


_install_fastapi_test_compat()


def _to_fastapi_path(rule: str) -> str:
    return re.sub(r"<(?:[^:>]+:)?([^>]+)>", r"{\1}", str(rule))


def _build_placeholder(rule: str, endpoint: str, methods=("GET",)):
    async def _placeholder(**_kwargs):
        return ""

    return _to_fastapi_path(rule), endpoint, list(methods), _placeholder


@pytest.fixture
def anime_factory():
    """Создает сущности Anime с переопределяемыми полями для тестов."""
    from backend.domain.anime.entity import Anime

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
    """Создает совместимый test-app для отдельных FastAPI routers."""

    def _build(*routers, user=None, container=None):
        app = FastAPI()
        app.mount(
            "/static",
            StaticFiles(directory=str(FRONTEND_ROOT / "static")),
            name="static",
        )
        app.add_middleware(
            SessionMiddleware,
            secret_key="test-secret",
            same_site="lax",
            session_cookie="aem_session",
        )

        candidate_modules = []
        for router in routers:
            app.include_router(router)
            for route in getattr(router, "routes", []):
                module_name = getattr(getattr(route, "endpoint", None), "__module__", None)
                if not module_name:
                    continue
                module = importlib.import_module(module_name)
                if module not in candidate_modules:
                    candidate_modules.append(module)

        @app.middleware("http")
        async def _inject_request_state(request, call_next):
            resolved_container = container
            if resolved_container is None:
                for module in candidate_modules:
                    module_container = getattr(module, "container", None)
                    if module_container is not None:
                        resolved_container = module_container
                        break
            request.state.user = user
            request.state.container = _wrap_test_container(resolved_container)
            request.state.clear_access_token_cookie = False
            request.state.db_session = None
            return await call_next(request)

        def _register_placeholder(rule, endpoint, methods=("GET",)):
            if any(getattr(route, "name", None) == endpoint for route in app.router.routes):
                return
            placeholder_rule, name, http_methods, handler = _build_placeholder(
                rule,
                endpoint,
                methods=methods,
            )
            app.add_api_route(
                placeholder_rule,
                handler,
                methods=http_methods,
                name=name,
            )

        _register_placeholder("/anime/search", "anime.search_anime_page")
        _register_placeholder("/anime/search/description", "anime.search_by_description_page")
        _register_placeholder("/highlights/{user_id}", "highlight.get_user_highlights")
        _register_placeholder("/highlights/top", "highlight.get_public_top_highlights")
        _register_placeholder("/highlights/feed", "highlight.get_highlight_feed")
        _register_placeholder("/highlights/following", "highlight.get_following_highlights")
        _register_placeholder("/highlights/saved", "highlight.get_saved_highlights")
        _register_placeholder("/highlights/liked", "highlight.get_liked_highlights")
        _register_placeholder("/highlights/notifications", "highlight.get_highlight_notifications")
        _register_placeholder("/favorites/{user_id}", "favorite.get_favorites")
        _register_placeholder("/collections", "collection.collections_page")
        _register_placeholder(
            "/collections/share/{collection_id}", "collection.shared_collection_page"
        )
        _register_placeholder("/auth/profile", "auth.profile_page")
        _register_placeholder("/auth/login", "auth.login_page")
        _register_placeholder("/auth/register", "auth.register_page")
        _register_placeholder("/auth/logout", "auth.logout_user", methods=("POST",))
        _register_placeholder("/support", "support.support_page")
        _register_placeholder("/users/{user_id}", "user.public_profile_page")
        _register_placeholder("/users/{user_id}/follow", "user.follow_user", methods=("POST",))
        _register_placeholder("/users/{user_id}/unfollow", "user.unfollow_user", methods=("POST",))
        _register_placeholder("/watch/{anime_id}", "watch.watch_page")
        _register_placeholder("/", "index.index")
        return CompatApp(app)

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
def run_async():
    def _run(awaitable):
        return asyncio.run(awaitable)

    return _run


@pytest.fixture
def db_session():
    """Создает изолированную sync SQLAlchemy-сессию в памяти для repository-тестов."""
    from backend.infrastructure.files.database import Base

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    session = session_local()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture
async def async_db_session_factory():
    """Создает async SQLAlchemy engine и sessionmaker на общей in-memory базе."""
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    from backend.infrastructure.files.database import Base

    engine = create_async_engine(
        "sqlite+aiosqlite://",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    session_local = async_sessionmaker(bind=engine, expire_on_commit=False)
    yield session_local
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def async_db_session():
    """Создает изолированную async SQLAlchemy-сессию в памяти для async repository-тестов."""
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    from backend.infrastructure.files.database import Base

    engine = create_async_engine(
        "sqlite+aiosqlite://",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    session_local = async_sessionmaker(bind=engine, expire_on_commit=False)
    async with session_local() as session:
        try:
            yield session
        finally:
            await session.close()
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
    await engine.dispose()
