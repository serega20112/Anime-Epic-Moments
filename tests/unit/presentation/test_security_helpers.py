from __future__ import annotations

import pytest
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, PlainTextResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from backend.application.interface.services import CSRFServiceInterface
from backend.application.policies import RequestPolicy
from backend.infrastructure.security.csrf_service import CSRFService
from backend.presentation.app_factory import _normalize_request_id, app_context_middleware
from backend.presentation.security_helpers import (
    TOKEN_SOURCE_BEARER,
    TOKEN_SOURCE_COOKIE,
    extract_bearer_token,
    get_allowed_origins,
    is_bearer_request,
    is_csrf_exempt,
    resolve_access_token,
)

TEST_CSRF_TOKEN = "test-csrf-token"


class _FakeContainer:
    """Заменяет request-scoped контейнер dishka: отдаёт зависимости по типу."""

    def __init__(self, providers: dict[type, object]) -> None:
        """Сохраняет карту «тип -> экземпляр».

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


async def setup_session(request):
    """Положить CSRF-токен в сессию клиента.

    Args:
        request: Текущий HTTP-запрос.

    Returns:
        PlainTextResponse: Ответ ``ok``.
    """
    request.session["csrf_token"] = TEST_CSRF_TOKEN
    return PlainTextResponse("ok")


async def echo_form(request):
    """Вернуть поле title из полученной формы.

    Args:
        request: Текущий HTTP-запрос.

    Returns:
        JSONResponse: Значение поля title.
    """
    form = await request.form()
    return JSONResponse({"title": form.get("title")})


def _make_app() -> Starlette:
    """Собрать приложение с боевой CSRF-мидлварей и контейнером зависимостей.

    Используется настоящая :func:`app_context_middleware`, а не её упрощённая копия:
    копия не покрывала ветку успешной проверки и пропустила регрессию, из-за которой
    все корректные POST падали с 500.

    Returns:
        Starlette: Приложение с маршрутами ``/setup`` и ``/echo``.
    """
    container = _FakeContainer(
        {
            CSRFServiceInterface: CSRFService(),
            RequestPolicy: RequestPolicy(
                max_request_bytes=1_048_576,
                base_url="https://app.example",
                allowed_origins=("https://cdn.example",),
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
            Route("/setup", setup_session, methods=["GET"]),
            Route("/echo", echo_form, methods=["POST"]),
        ],
        middleware=[
            Middleware(SessionMiddleware, secret_key="test-secret"),
            Middleware(BaseHTTPMiddleware, dispatch=inject_container),
            Middleware(BaseHTTPMiddleware, dispatch=app_context_middleware),
        ],
    )


@pytest.mark.unit
def test_validate_csrf_keeps_form_fields_for_downstream_route():
    """Проверяем, что после validate_csrf в мидлвари роут получает полную форму.

    Регрессия: validate_csrf вызывал request.form() напрямую, Starlette
    BaseHTTPMiddleware при этом потреблял stream и вниз уходил пустой body —
    все поля формы терялись (например, название коллекции приходило пустым
    и падала доменная валидация «от 1 до 80 символов»).
    """
    client = TestClient(_make_app())
    client.get("/setup")

    response = client.post(
        "/echo",
        data={"csrf_token": TEST_CSRF_TOKEN, "title": "Новая коллекция"},
    )

    assert response.status_code == 200
    assert response.json()["title"] == "Новая коллекция"


@pytest.mark.unit
def test_validate_csrf_rejects_form_without_matching_token():
    """Проверяем, что форма с неверным csrf_token по-прежнему отклоняется."""
    client = TestClient(_make_app())
    client.get("/setup")

    response = client.post(
        "/echo",
        data={"csrf_token": "wrong-token", "title": "Новая коллекция"},
    )

    assert response.status_code == 403


@pytest.mark.unit
async def test_auth_paths_are_not_csrf_exempt():
    """Проверяем, что /auth-маршруты больше не освобождены от CSRF-проверки."""
    request = _build_request("/auth/login", method="POST")

    assert await is_csrf_exempt(request) is False


@pytest.mark.unit
async def test_static_and_media_proxy_remain_csrf_exempt():
    """Проверяем, что static и media proxy остаются CSRF-exempt."""
    static_request = _build_request("/static/js/core.js", method="POST")
    proxy_request = _build_request("/watch/proxy", method="POST")

    assert await is_csrf_exempt(static_request) is True
    assert await is_csrf_exempt(proxy_request) is True


@pytest.mark.unit
async def test_api_token_routes_are_csrf_exempt():
    """Что тестируем: освобождение выпусков и отзыва токенов от CSRF.

    Что передаём: POST на /api/v1/auth/token и на страницу профиля API.
    Что ожидаем: маршруты токенов освобождены, посторонний путь внутри /api — нет.
    """
    token_request = _build_request("/api/v1/auth/token", method="POST")
    other_request = _build_request("/api/v1/recommendations/generate/5", method="POST")

    assert await is_csrf_exempt(token_request) is True
    assert await is_csrf_exempt(other_request) is False


@pytest.mark.unit
class TestBearerTokenExtraction:
    """Юнит-тесты единого разбора access-токена из заголовка и cookie."""

    def test_extracts_token_from_authorization_header(self):
        """Что тестируем: извлечение Bearer-токена из заголовка.
        Что передаём: заголовок с произвольным регистром схемы и лишними пробелами.
        Что ожидаем: голое значение токена без префикса.
        """
        request = _build_request(
            "/api/v1/auth/token/revoke", headers={"Authorization": "Bearer  abc123 "}
        )

        assert extract_bearer_token(request) == "abc123"
        assert is_bearer_request(request) is True

    @pytest.mark.parametrize(
        "header_value",
        [None, "", "Basic abc123", "Bearer", "Bearer    "],
    )
    def test_rejects_missing_or_foreign_scheme(self, header_value):
        """Что тестируем: отсутствие заголовка и чужая схема аутентификации.
        Что передаём: пустой заголовок, Basic и битый Bearer без значения.
        Что ожидаем: None и признак не-Bearer запроса.
        """
        headers = {} if header_value is None else {"Authorization": header_value}
        request = _build_request("/api/v1/auth/token/revoke", headers=headers)

        assert extract_bearer_token(request) is None
        assert is_bearer_request(request) is False

    def test_bearer_wins_over_cookie(self):
        """Что тестируем: источник токена при обоих заполненных значениях.
        Что передаём: заголовок Bearer и cookie access_token.
        Что ожидаем: значение из заголовка, источник — bearer.
        """
        request = _build_request("/watch/19", headers={"Authorization": "Bearer bearer-token"})
        request.scope["headers"].append((b"cookie", b"access_token=cookie-token"))

        assert resolve_access_token(request) == ("bearer-token", TOKEN_SOURCE_BEARER)

    def test_falls_back_to_cookie(self):
        """Что тестируем: cookie-схему браузера без заголовка.
        Что передаём: только cookie access_token.
        Что ожидаем: значение из cookie и источник cookie.
        """
        request = _build_request("/watch/19")
        request.scope["headers"].append((b"cookie", b"access_token=cookie-token"))

        assert resolve_access_token(request) == ("cookie-token", TOKEN_SOURCE_COOKIE)

    def test_guest_request_yields_empty_token(self):
        """Что тестируем: запрос гостя без токена вообще.
        Что передаём: пустые заголовок и cookie.
        Что ожидаем: пустую строку токена, чтобы вызывающий код не ветвился на None.
        """
        assert resolve_access_token(_build_request("/watch/19")) == ("", TOKEN_SOURCE_COOKIE)


@pytest.mark.unit
async def test_allowed_origins_ignore_request_host():
    """Что тестируем: allowed origins строятся из конфигурации, а не из Host запроса.

    Что передаём: политику с базовым origin и списком дополнительных origin.
    Что ожидаем: оба origin из политики, и origin, производный от Host
    (``http://testserver``), среди разрешённых отсутствует.
    """
    request = _build_request("/", method="POST")
    request.state.dishka_container = _FakeContainer(
        {
            RequestPolicy: RequestPolicy(
                max_request_bytes=1_048_576,
                base_url="https://trusted.example",
                allowed_origins=("https://cdn.example",),
            )
        }
    )

    origins = await get_allowed_origins(request)

    assert "https://trusted.example" in origins
    assert "https://cdn.example" in origins
    assert "http://testserver" not in origins


def _build_request(
    path: str, method: str = "GET", headers: dict[str, str] | None = None
) -> Request:
    """Собрать минимальный HTTP-запрос для проверки security-хелперов.

    Args:
        path: Путь запроса.
        method: HTTP-метод запроса.
        headers: Дополнительные заголовки запроса.

    Returns:
        Request: Объект запроса с переданными заголовками.
    """
    scope = {
        "type": "http",
        "method": method,
        "path": path,
        "raw_path": path.encode("utf-8"),
        "query_string": b"",
        "headers": [
            (name.lower().encode("latin-1"), value.encode("latin-1"))
            for name, value in (headers or {}).items()
        ],
        "client": ("203.0.113.9", 12345),
        "server": ("testserver", 80),
        "scheme": "http",
        "root_path": "",
    }
    return Request(scope)


@pytest.mark.unit
def test_body_limit_middleware_rejects_oversized_chunked_body():
    """Проверяем, что BodyLimitMiddleware режет тело больше лимита без Content-Length."""
    from backend.presentation.app_factory import BodyLimitMiddleware

    async def echo(request):
        """Прочитать тело запроса и вернуть его размер.

        Args:
            request: Текущий HTTP-запрос.

        Returns:
            PlainTextResponse: Длина полученного тела.
        """
        body = await request.body()
        return PlainTextResponse(str(len(body)))

    app = Starlette(routes=[Route("/echo", echo, methods=["POST"])])
    app.add_middleware(BodyLimitMiddleware, max_bytes=64)
    client = TestClient(app)

    response = client.post("/echo", content=b"x" * 128)

    assert response.status_code == 413


@pytest.mark.unit
@pytest.mark.parametrize(
    ("raw_value", "expected"),
    [
        ("abc-123_456", "abc-123_456"),
        ("trace.id-7", "trace.id-7"),
        ("!!!bad!!!", None),
        ("", None),
        (None, None),
        ("x" * 65, None),
        ("  abc-123  ", "abc-123"),
        ("привет", None),
    ],
)
def test_normalize_request_id_passes_only_safe_values(raw_value, expected):
    """Что тестируем: функцию _normalize_request_id.

    Что передаём: заголовок X-Request-ID клиента — валидный, пустой, слишком
    длинный, с недопустимыми символами и с обрамляющими пробелами.
    Что ожидаем: безопасное значение проходит как есть, всё остальное
    заменяется сгенерированным 16-символьным hex-идентификатором.
    """
    result = _normalize_request_id(raw_value)

    if expected is None:
        assert len(result) == 16
        assert all(char in "0123456789abcdef" for char in result)
    else:
        assert result == expected


@pytest.mark.unit
def test_generated_request_id_is_unique():
    """Что тестируем: генерацию идентификатора при недопустимом входе.

    Что передаём: два вызова с заведомо плохим значением заголовка.
    Что ожидаем: сгенерированные идентификаторы различаются, в логи не
    протаскивается клиентское значение.
    """
    assert _normalize_request_id("!!!bad!!!") != _normalize_request_id("!!!bad!!!")
