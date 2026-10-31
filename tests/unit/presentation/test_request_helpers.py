from __future__ import annotations

from types import SimpleNamespace

import pytest
from starlette.requests import Request

from backend.presentation.api.errors import expects_json
from backend.presentation.api.helpers import get_current_user, wants_json


def _build_request(
    body: bytes,
    content_type: str | None = None,
    accept: str | None = None,
    path: str = "/echo",
) -> Request:
    """Собрать HTTP-запрос с указанным телом, заголовками и путём.

    Args:
        body: Байты тела запроса.
        content_type: Значение заголовка Content-Type, если нужно.
        accept: Значение заголовка Accept, если нужно.
        path: Путь запроса, влияющий на выбор формата ответа.

    Returns:
        Request: Объект запроса для вызова хелперов.
    """
    headers = []
    if content_type is not None:
        headers.append((b"content-type", content_type.encode("latin-1")))
    if accept is not None:
        headers.append((b"accept", accept.encode("latin-1")))
    scope = {
        "type": "http",
        "method": "POST",
        "path": path,
        "raw_path": path.encode("latin-1"),
        "query_string": b"",
        "headers": headers,
        "client": ("203.0.113.9", 12345),
        "server": ("testserver", 80),
        "scheme": "http",
        "root_path": "",
    }
    request = Request(scope)
    request._body = body
    return request


@pytest.mark.unit
class TestWantsJson:
    """Юнит-тесты определения ожидаемого формата ответа."""

    @pytest.mark.parametrize(
        ("accept", "content_type", "expected"),
        [
            ("application/json", None, True),
            ("text/html", "application/json", True),
            ("text/html,application/xhtml+xml", None, False),
            (None, None, False),
        ],
    )
    def test_detects_json_expectation(self, accept, content_type, expected):
        """Что тестируем: wants_json по заголовкам запроса.
        Что передаём: комбинации Accept и Content-Type.
        Что ожидаем: True только когда клиент явно рассчитывает на JSON.
        """
        assert wants_json(_build_request(b"{}", content_type, accept)) is expected


@pytest.mark.unit
class TestExpectsJson:
    """Юнит-тесты выбора формата тела ошибки для JSON API."""

    def test_api_path_prefers_json_without_accept_header(self):
        """Что тестируем: отказ на пути из JSON API без заголовка Accept.
        Что передаём: запрос к /api/v1/... с Accept по умолчанию.
        Что ожидаем: True, чтобы мобильный клиент получил машиночитаемое тело.
        """
        request = _build_request(b"{}", path="/api/v1/auth/token")

        assert expects_json(request) is True
        assert wants_json(request) is False

    def test_html_page_path_keeps_accept_signal(self):
        """Что тестируем: обычный путь страницы.
        Что передаём: браузерный запрос на /watch/19 без JSON в Accept.
        Что ожидаем: False, чтобы отказом осталась HTML-страница.
        """
        assert expects_json(_build_request(b"{}", accept="text/html", path="/watch/19")) is False


@pytest.mark.unit
class TestGetCurrentUser:
    """Юнит-тесты чтения пользователя из состояния запроса."""

    async def test_returns_user_from_state(self):
        """Что тестируем: пользователя из состояния запроса.
        Что передаём: запрос с request.state.user.
        Что ожидаем: тот же объект пользователя.
        """
        request = _build_request(b"{}")
        user = SimpleNamespace(id=7)
        request.state.user = user

        assert await get_current_user(request) is user

    async def test_returns_none_for_guest(self):
        """Что тестируем: запрос без аутентификации.
        Что передаём: запрос без request.state.user.
        Что ожидаем: None вместо исключения.
        """
        assert await get_current_user(_build_request(b"{}")) is None
