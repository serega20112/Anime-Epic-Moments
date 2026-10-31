"""Регрессионные тесты боевой мидлвари контекста запроса.

Вызывается настоящая :func:`backend.presentation.app_factory.app_context_middleware`,
а не её копия: раньше тесты воспроизводили CSRF-проверку локальным
``CsrfMiddleware``, из-за чего ветка успешной проверки (обязанная передать управление
маршруту) не исполнялась ни одним тестом, и падение каждого успешного POST с
``UnboundLocalError: response`` дошло до запуска.
"""

from __future__ import annotations

from functools import partial
from http import HTTPStatus

import pytest
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import JSONResponse, PlainTextResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from backend.application.interface.services import CSRFServiceInterface
from backend.application.policies import CookiePolicy, RequestPolicy
from backend.infrastructure.security.csrf_service import CSRFService
from backend.presentation.app_factory import app_context_middleware

BASE_URL = "https://app.example"
ROUTE_RAN = "handler_ran"


class _FakeContainer:
    """Заменяет request-scoped контейнер dishka: отдаёт зависимости по типу."""

    def __init__(self, providers: dict[type, object]) -> None:
        """Сохранить карту «тип -> экземпляр».

        Args:
            providers: Доступные для разрешения зависимости.
        """
        self._providers = providers

    async def get(self, dependency: type) -> object:
        """Разрешить зависимость по типу.

        Args:
            dependency: Запрашиваемый тип.

        Returns:
            object: Зарегистрированный экземпляр.

        Raises:
            KeyError: Тип не зарегистрирован.
        """
        return self._providers[dependency]


class _Calls:
    """Фиксирует, дошёл ли запрос до маршрута и с какими флагами."""

    def __init__(self) -> None:
        """Инициализировать пустой журнал вызовов."""
        self.route_invocations = 0
        self.clear_cookie_requested = False


async def _issue_csrf_token(request):
    """Выдать клиенту настоящий CSRF-токен, положив его в сессию.

    Args:
        request: Текущий HTTP-запрос.

    Returns:
        PlainTextResponse: Значение токена для подстановки в форму.
    """
    service = await request.state.dishka_container.get(CSRFServiceInterface)
    token = service.generate_token()
    request.session["csrf_token"] = token.to_session()
    return PlainTextResponse(token.value)


async def _login_handler(request, calls: _Calls):
    """Сымитировать обработчик POST-маршрута авторизации.

    Args:
        request: Текущий HTTP-запрос.
        calls: Журнал вызовов маршрута.

    Returns:
        PlainTextResponse: Ответ маршрута, оформленный мидлварей.
    """
    calls.route_invocations += 1
    if calls.clear_cookie_requested:
        request.state.clear_access_token_cookie = True
    return PlainTextResponse(ROUTE_RAN)


async def _json_handler(request, calls: _Calls):
    """Сымитировать JSON-обработчик маршрута записи.

    Args:
        request: Текущий HTTP-запрос.
        calls: Журнал вызовов маршрута.

    Returns:
        JSONResponse: Эхо отправленного поля.
    """
    calls.route_invocations += 1
    payload = await request.json()
    return JSONResponse({"title": payload.get("title")})


def _make_app(
    calls: _Calls,
    *,
    max_request_bytes: int = 1_048_576,
    cookie_secure: bool = False,
) -> Starlette:
    """Собрать Starlette-приложение с настоящим порядком мидлварей.

    Порядок повторяет ``create_app``: ``SessionMiddleware`` внешним слоем, затем
    внедрение контейнера, затем проверяющая мидлваря — так же, как в боевом приложении.

    Args:
        calls: Журнал вызовов маршрута для последующих проверок.
        max_request_bytes: Разрешённый размер тела запроса из политики.
        cookie_secure: Флаг безопасных cookie, включающий HSTS.

    Returns:
        Starlette: Приложение с маршрутами выдачи токена и записи.
    """
    container = _FakeContainer(
        {
            CSRFServiceInterface: CSRFService(),
            RequestPolicy: RequestPolicy(
                max_request_bytes=max_request_bytes,
                base_url=BASE_URL,
                allowed_origins=("https://cdn.example",),
                cookie_secure=cookie_secure,
                hsts_max_age=63_072_000,
            ),
            CookiePolicy: CookiePolicy(
                secure=cookie_secure,
                samesite="Lax",
                domain=None,
                access_expire_minutes=30,
                refresh_expire_days=30,
            ),
        }
    )

    async def inject_container(request, call_next):
        """Прикрепить контейнер dishka к запросу.

        Args:
            request: Текущий HTTP-запрос.
            call_next: Следующий шаг обработки.

        Returns:
            Response: Ответ следующего шага.
        """
        request.state.dishka_container = container
        return await call_next(request)

    return Starlette(
        routes=[
            Route("/csrf", _issue_csrf_token, methods=["GET"]),
            Route("/auth/login", partial(_login_handler, calls=calls), methods=["POST"]),
            Route("/auth/json", partial(_json_handler, calls=calls), methods=["POST"]),
        ],
        middleware=[
            Middleware(SessionMiddleware, secret_key="test-secret"),
            Middleware(BaseHTTPMiddleware, dispatch=inject_container),
            Middleware(BaseHTTPMiddleware, dispatch=app_context_middleware),
        ],
    )


def _client(calls: _Calls, **kwargs) -> TestClient:
    """Создать тестовый клиент и получить CSRF-токен в сессию.

    Args:
        calls: Журнал вызовов маршрута.
        **kwargs: Параметры сборки приложения (лимит тела, secure-флаги).

    Returns:
        TestClient: Клиент с уже сохранённым в cookie-джар токеном.
    """
    client = TestClient(_make_app(calls, **kwargs))
    response = client.get("/csrf")
    assert response.status_code == HTTPStatus.OK
    client.csrf_token = response.text
    return client


@pytest.mark.unit
def test_successful_csrf_post_reaches_route_and_gets_security_headers():
    """Регрессия: успешная CSRF-проверка обязана вызвать маршрут, а не падать.

    До исправления в этой ветке ``response`` не присваивался, и мидлваря падала с
    ``UnboundLocalError`` — любой корректно отправленный POST (логин, регистрация,
    создание коллекции) давал 500.
    """
    calls = _Calls()
    client = _client(calls)

    response = client.post(
        "/auth/login",
        data={"csrf_token": client.csrf_token, "email": "a@b.com"},
    )

    assert response.status_code == HTTPStatus.OK
    assert response.text == ROUTE_RAN
    assert calls.route_invocations == 1
    assert response.headers["X-Frame-Options"] == "DENY"
    assert "form-action 'self'" in response.headers["Content-Security-Policy"]
    assert "Strict-Transport-Security" not in response.headers


@pytest.mark.unit
def test_post_without_valid_csrf_token_is_rejected_before_route():
    """Неверный токен отклоняется до маршрута, маршрут не исполняется."""
    calls = _Calls()
    client = _client(calls)

    response = client.post("/auth/login", data={"csrf_token": "wrong", "email": "a@b.com"})

    assert response.status_code == HTTPStatus.FORBIDDEN
    assert response.text == "CSRF validation failed"
    assert calls.route_invocations == 0


@pytest.mark.unit
def test_json_post_with_header_token_reaches_route():
    """API-клиент передаёт токен заголовком и получает ответ маршрута."""
    calls = _Calls()
    client = _client(calls)

    response = client.post(
        "/auth/json",
        json={"title": "Хайлайт"},
        headers={"X-CSRF-Token": client.csrf_token},
    )

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {"title": "Хайлайт"}
    assert calls.route_invocations == 1


@pytest.mark.unit
def test_cross_origin_post_is_rejected_before_route():
    """Запись с чужого origin отклоняется до CSRF-проверки и до маршрута."""
    calls = _Calls()
    client = _client(calls)

    response = client.post(
        "/auth/login",
        data={"csrf_token": client.csrf_token},
        headers={"Origin": "https://evil.example"},
    )

    assert response.status_code == HTTPStatus.FORBIDDEN
    assert response.json()["code"] == "forbidden_origin"
    assert calls.route_invocations == 0


@pytest.mark.unit
def test_same_origin_post_from_allowed_list_reaches_route():
    """Origin из белого списка проходит проверку так же, как запрос без Origin."""
    calls = _Calls()
    client = _client(calls)

    response = client.post(
        "/auth/login",
        data={"csrf_token": client.csrf_token},
        headers={"Origin": "https://cdn.example"},
    )

    assert response.status_code == HTTPStatus.OK
    assert calls.route_invocations == 1


@pytest.mark.unit
def test_oversized_body_returns_413_without_calling_route():
    """Тело больше лимита политики отсекается с 413 до обращения к маршруту."""
    calls = _Calls()
    client = _client(calls, max_request_bytes=8)

    response = client.post(
        "/auth/login",
        data={"csrf_token": client.csrf_token, "email": "someone@example.com"},
    )

    assert response.status_code == HTTPStatus.REQUEST_ENTITY_TOO_LARGE
    assert calls.route_invocations == 0


@pytest.mark.unit
def test_revoked_token_flag_clears_cookie_on_route_response():
    """Флаг из маршрута приводит к удалению cookie на выходе из мидлвари."""
    calls = _Calls()
    calls.clear_cookie_requested = True
    client = _client(calls)

    response = client.post("/auth/login", data={"csrf_token": client.csrf_token})

    assert response.status_code == HTTPStatus.OK
    set_cookie = response.headers["set-cookie"]
    assert 'access_token=""' in set_cookie
    assert "Max-Age=0" in set_cookie


@pytest.mark.unit
def test_secure_policy_adds_hsts_to_route_response():
    """При ``cookie_secure`` ответ получает HSTS-заголовок из политики."""
    calls = _Calls()
    client = _client(calls, cookie_secure=True)

    response = client.post("/auth/login", data={"csrf_token": client.csrf_token})

    assert response.status_code == HTTPStatus.OK
    assert response.headers["Strict-Transport-Security"].startswith("max-age=63072000")
