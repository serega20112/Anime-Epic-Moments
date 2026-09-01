"""Template rendering utilities with Jinja2, session flash messages, and CSRF token injection."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

from fastapi import Request
from fastapi.responses import HTMLResponse
from jinja2 import Environment, FileSystemLoader, select_autoescape

PROJECT_ROOT = Path(__file__).resolve().parents[4]
TEMPLATES_ROOT = PROJECT_ROOT / "src" / "frontend" / "templates"

_environment = Environment(
    loader=FileSystemLoader(str(TEMPLATES_ROOT)),
    autoescape=select_autoescape(("html", "xml")),
)


def _time_ago(value: Any) -> str:
    """Format a datetime as a short relative time for templates.

    Times within the last day are rendered in Russian relative form
    ("5 минут назад"), older timestamps fall back to a date and time.

    Args:
        value: Datetime or string to format.

    Returns:
        str: Human readable timestamp.
    """
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(str(value))
        except ValueError:
            return str(value)
    if not isinstance(value, datetime):
        return str(value)
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    delta = (datetime.now(UTC) - value).total_seconds()
    if delta < 0:
        return value.strftime("%Y-%m-%d %H:%M")
    if delta < 60:
        return "только что"
    minutes = max(1, int(delta // 60))
    if minutes < 60:
        return f"{minutes} мин назад"
    hours = max(1, int(minutes // 60))
    if hours < 24:
        return f"{hours} ч назад"
    return value.strftime("%Y-%m-%d %H:%M")


_environment.filters["time_ago"] = _time_ago

_route_param_names_cache: dict[str, set[str]] = {}


def _get_session(request: Request) -> dict[str, Any] | None:
    """Retrieve session dictionary from request scope.

    Args:
        request: Current HTTP request.

    Returns:
        dict[str, Any] | None: Session data or None if not available.
    """
    session = request.scope.get("session")
    return session if isinstance(session, dict) else None


async def flash(request: Request, message: str):
    """Add a flash message to the session for display on the next page load.

    Args:
        request: Current HTTP request.
        message: Message text to flash.
    """
    session = _get_session(request)
    if session is None:
        return
    messages = list(session.get("_flashes", []))
    messages.append(str(message))
    session["_flashes"] = messages


async def pop_flashed_messages(request: Request) -> list[str]:
    """Retrieve and clear all flash messages from the session.

    Args:
        request: Current HTTP request.

    Returns:
        list[str]: List of flashed messages.
    """
    session = _get_session(request)
    if session is None:
        return []
    messages = session.pop("_flashes", [])
    if not isinstance(messages, list):
        return []
    return [str(item) for item in messages if str(item).strip()]


@dataclass(slots=True)
class TemplateRequestProxy:
    """Proxy object exposing request properties to Jinja2 templates."""

    request: Request

    @property
    def url(self) -> str:
        """Full request URL."""
        return str(self.request.url)

    @property
    def path(self) -> str:
        """Request path component."""
        return self.request.url.path

    @property
    def referrer(self) -> str | None:
        """Referer header value."""
        value = self.request.headers.get("referer")
        return str(value).strip() if value else None

    def url_for(self, name: str, **params: Any) -> str:
        """Generate a URL for a named route with path and query parameters.

        Args:
            name: Route name.
            **params: Path and query parameters.

        Returns:
            str: Generated URL.
        """
        if name == "static":
            path = str(params.pop("filename", params.pop("path", ""))).lstrip("/")
            return str(self.request.app.url_path_for("static", path=path))
        path_param_names = self._get_route_param_names(name)
        path_params = {
            key: str(value)
            for key, value in params.items()
            if key in path_param_names and value is not None
        }
        query_params = {
            key: self._normalize_query_value(value)
            for key, value in params.items()
            if key not in path_param_names and value is not None
        }
        path = str(self.request.app.url_path_for(name, **path_params))
        if not query_params:
            return path
        return f"{path}?{urlencode(query_params, doseq=True)}"

    def _get_route_param_names(self, name: str) -> set[str]:
        """Get parameter names for a named route.

        Args:
            name: Route name.

        Returns:
            set[str]: Set of path parameter names.
        """
        cached = _route_param_names_cache.get(name)
        if cached is not None:
            return cached
        for route in self.request.app.router.routes:
            if getattr(route, "name", None) != name:
                continue
            param_names = set(getattr(route, "param_convertors", {}).keys())
            _route_param_names_cache[name] = param_names
            return param_names
        return set()

    def _normalize_query_value(self, value: Any) -> str | list[str]:
        """Normalize a query parameter value for URL encoding.

        Args:
            value: Raw parameter value.

        Returns:
            str | list[str]: Normalized value.
        """
        if isinstance(value, (list, tuple, set)):
            return [str(item) for item in value]
        return str(value)


async def render_template(
    request: Request,
    template_name: str,
    *,
    status_code: int = 200,
    headers: dict[str, str] | None = None,
    **context: Any,
) -> HTMLResponse:
    """Render a Jinja2 template with request context and flash messages.

    Injects current_user, url_for, csrf_token, and get_flashed_messages
    into the template context.

    Args:
        request: Current HTTP request.
        template_name: Template file path relative to templates root.
        status_code: HTTP status code for the response.
        headers: Additional response headers.
        **context: Additional template variables.

    Returns:
        HTMLResponse: Rendered HTML response.
    """
    proxy = TemplateRequestProxy(request)
    messages = await pop_flashed_messages(request)

    def get_flashed_messages() -> list[str]:
        return list(messages)

    def url_for(name: str, **params: Any) -> str:
        return proxy.url_for(name, **params)

    def csrf_token() -> str:
        """Get the current CSRF token value for use in forms."""
        session = request.scope.get("session")
        if isinstance(session, dict):
            token = session.get("csrf_token")
            if isinstance(token, str):
                return token
        token_data = getattr(request.state, "csrf_token", None)
        if token_data and isinstance(token_data, dict):
            return token_data.get("value", "")
        return getattr(request.state, "csrf_token", "") or ""

    template = _environment.get_template(template_name)
    html = template.render(
        request=proxy,
        current_user=getattr(request.state, "user", None),
        get_flashed_messages=get_flashed_messages,
        url_for=url_for,
        csrf_token=csrf_token,
        **context,
    )
    return HTMLResponse(content=html, status_code=status_code, headers=headers)
