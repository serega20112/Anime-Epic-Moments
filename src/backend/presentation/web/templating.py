"""Рендеринг Jinja2-шаблонов с flash-сообщениями и CSRF-токеном.

Отрисовка страниц — забота presentation-слоя, а не инфраструктуры: здесь нет
внешних систем, только HTTP-ответ и шаблоны фронтенда. Поэтому модуль живёт в
``presentation/web``, и роуты импортируют его без обращения к инфраструктуре.
"""

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

FLASHES_KEY = "_flashes"
STATIC_ROUTE_NAME = "static"


def _time_ago(value: Any) -> str:
    """Отформатировать дату как короткое относительное время.

    Значения за последний час показываются по-русски («5 минут назад»), более
    старые — датой и временем, чтобы в ленте не появлялось «1000 ч назад».

    Args:
        value: DateTime либо ISO-строка.

    Returns:
        str: Человекочитаемая отметка времени.
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
    """Достать словарь сессии из ASGI-scope запроса.

    Args:
        request: Текущий HTTP-запрос.

    Returns:
        dict[str, Any] | None: Данные сессии либо None, если сессии нет.
    """
    session = request.scope.get("session")
    return session if isinstance(session, dict) else None


async def flash(request: Request, message: str):
    """Положить сообщение во внутри-сессонный список flash.

    Args:
        request: Текущий HTTP-запрос.
        message: Текст сообщения.
    """
    session = _get_session(request)
    if session is None:
        return
    messages = list(session.get(FLASHES_KEY, []))
    messages.append(str(message))
    session[FLASHES_KEY] = messages


async def pop_flashed_messages(request: Request) -> list[str]:
    """Забрать и очистить все flash-сообщения сессии.

    Args:
        request: Текущий HTTP-запрос.

    Returns:
        list[str]: Непустые сообщения; пустой список, если сессии нет.
    """
    session = _get_session(request)
    if session is None:
        return []
    messages = session.pop(FLASHES_KEY, [])
    if not isinstance(messages, list):
        return []
    return [str(item) for item in messages if str(item).strip()]


@dataclass(slots=True)
class TemplateRequestProxy:
    """Обёртка запроса, отдающая шаблонам безопасный набор свойств."""

    request: Request

    @property
    def url(self) -> str:
        """Полный URL запроса."""
        return str(self.request.url)

    @property
    def path(self) -> str:
        """Путь запроса без домена и запросной строки."""
        return self.request.url.path

    @property
    def referrer(self) -> str | None:
        """Значение заголовка Referer либо None."""
        value = self.request.headers.get("referer")
        return str(value).strip() if value else None

    def url_for(self, name: str, **params: Any) -> str:
        """Построить URL именованного маршрута из path- и query-параметров.

        Имена параметров сравниваются с параметрами маршрута: всё, что маршрутом
        не принимается, уходит в запросную строку. Так шаблон не может
        «молча» потерять обязательный path-параметр.

        Args:
            name: Имя маршрута.
            **params: Параметры пути и запросной строки.

        Returns:
            str: Построенный URL.
        """
        if name == STATIC_ROUTE_NAME:
            path = str(params.pop("filename", params.pop("path", ""))).lstrip("/")
            return str(self.request.app.url_path_for(STATIC_ROUTE_NAME, path=path))
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
        """Собрать имена path-параметров маршрута.

        Args:
            name: Имя маршрута.

        Returns:
            set[str]: Имена параметров; пустое множество, если маршрут неизвестен.
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
        """Привести значение query-параметра к строке либо списку строк.

        Args:
            value: Исходное значение параметра.

        Returns:
            str | list[str]: Значение, пригодное для urlencoded-развёртки.
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
    """Отрисовать Jinja2-шаблон с контекстом запроса.

    В контекст добавляются ``current_user``, ``url_for``, ``csrf_token`` и
    ``get_flashed_messages`` — без этого каждый шаблон повторял бы одинаковую
    подготовительную работу.

    Args:
        request: Текущий HTTP-запрос.
        template_name: Путь шаблона относительно корня шаблонов.
        status_code: HTTP-код ответа.
        headers: Дополнительные заголовки ответа.
        **context: Дополнительные переменные шаблона.

    Returns:
        HTMLResponse: Отрисованный HTML-ответ.
    """
    proxy = TemplateRequestProxy(request)
    messages = await pop_flashed_messages(request)

    def get_flashed_messages() -> list[str]:
        """Вернуть сообщения flash, изъятые из сессии."""
        return list(messages)

    def url_for(name: str, **params: Any) -> str:
        """Построить URL маршрута для шаблона.

        Args:
            name: Имя маршрута.
            **params: Параметры пути и запросной строки.

        Returns:
            str: Построенный URL.
        """
        return proxy.url_for(name, **params)

    def csrf_token() -> str:
        """Вернуть значение CSRF-токена для вставки в форму."""
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
