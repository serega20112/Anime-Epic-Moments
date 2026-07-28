from __future__ import annotations

from dataclasses import dataclass
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


def _get_session(request: Request) -> dict[str, Any] | None:
    session = request.scope.get("session")
    return session if isinstance(session, dict) else None


def flash(request: Request, message: str):
    session = _get_session(request)
    if session is None:
        return
    messages = list(session.get("_flashes", []))
    messages.append(str(message))
    session["_flashes"] = messages


def pop_flashed_messages(request: Request) -> list[str]:
    session = _get_session(request)
    if session is None:
        return []
    messages = session.pop("_flashes", [])
    if not isinstance(messages, list):
        return []
    return [str(item) for item in messages if str(item).strip()]


@dataclass(slots=True)
class TemplateRequestProxy:
    request: Request

    @property
    def url(self) -> str:
        return str(self.request.url)

    @property
    def path(self) -> str:
        return self.request.url.path

    @property
    def referrer(self) -> str | None:
        value = self.request.headers.get("referer")
        return str(value).strip() if value else None

    def url_for(self, name: str, **params: Any) -> str:
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
        for route in self.request.app.router.routes:
            if getattr(route, "name", None) != name:
                continue
            return set(getattr(route, "param_convertors", {}).keys())
        return set()

    def _normalize_query_value(self, value: Any):
        if isinstance(value, (list, tuple, set)):
            return [str(item) for item in value]
        return str(value)


def render_template(
    request: Request,
    template_name: str,
    *,
    status_code: int = 200,
    headers: dict[str, str] | None = None,
    **context: Any,
) -> HTMLResponse:
    proxy = TemplateRequestProxy(request)
    messages = pop_flashed_messages(request)

    def get_flashed_messages() -> list[str]:
        return list(messages)

    def url_for(name: str, **params: Any) -> str:
        return proxy.url_for(name, **params)

    def csrf_token() -> str:
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
