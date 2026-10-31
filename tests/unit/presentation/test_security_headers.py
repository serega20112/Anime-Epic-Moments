from __future__ import annotations

import pytest
from fastapi import Request
from starlette.responses import PlainTextResponse

from backend.application.policies import RequestPolicy
from backend.presentation.security_helpers import apply_security_headers

CSP_DIRECTIVES = ("script-src", "style-src", "default-src", "frame-ancestors")


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


def _build_request(policy: RequestPolicy) -> Request:
    """Собрать запрос, в state которого положен контейнер с политикой.

    Args:
        policy: Проверяемая политика HTTP-запроса.

    Returns:
        Request: Запрос с готовым `dishka_container`.
    """
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "raw_path": b"/",
        "query_string": b"",
        "headers": [],
        "client": ("203.0.113.9", 12345),
        "server": ("testserver", 80),
        "scheme": "http",
        "root_path": "",
    }
    request = Request(scope)
    request.state.dishka_container = _FakeContainer({RequestPolicy: policy})
    return request


async def _headers(*, cookie_secure: bool) -> dict[str, str]:
    """Проставить заголовки безопасности и вернуть их словарь.

    Args:
        cookie_secure: Значение ``cookie_secure`` проверяемой политики.

    Returns:
        dict[str, str]: Заголовки ответа после применения политики.
    """
    policy = RequestPolicy(
        max_request_bytes=1_048_576,
        base_url="https://app.example",
        hsts_max_age=63_072_000,
        cookie_secure=cookie_secure,
    )
    response = PlainTextResponse("ok")

    await apply_security_headers(_build_request(policy), response)
    return dict(response.headers)


@pytest.mark.unit
class TestContentSecurityPolicy:
    """Юнит-тесты политики CSP (задача S3.2)."""

    async def test_script_src_has_no_unsafe_eval(self):
        """Что тестируем: директиву script-src.
        Что передаём: любой ответ после применения заголовков.
        Что ожидаем: ``'unsafe-eval'`` отсутствует — собственный JS не использует
        eval, и подключать его из сети нечего.
        """
        headers = await _headers(cookie_secure=False)

        csp = headers["content-security-policy"]
        script_src = next(part for part in csp.split("; ") if part.startswith("script-src"))
        assert "'unsafe-eval'" not in script_src
        assert "'self'" in script_src

    async def test_frames_and_base_uri_are_locked(self):
        """Что тестируем: запрещённые источники для фреймов и базы.
        Что передаём: ответ после применения заголовков.
        Что ожидаем: ``frame-ancestors 'none'``, ``base-uri 'self'``,
        ``form-action 'self'`` — без них CSP не закрывает кликджекинг и
        подмену базы документа.
        """
        headers = await _headers(cookie_secure=False)

        csp = headers["content-security-policy"]
        for directive in CSP_DIRECTIVES:
            assert directive in csp
        assert "frame-ancestors 'none'" in csp
        assert "base-uri 'self'" in csp
        assert "form-action 'self'" in csp


@pytest.mark.unit
class TestTransportAndClickjackingHeaders:
    """Юнит-тесты HSTS и защищающих заголовков ответа."""

    async def test_hsts_applies_only_when_cookies_are_secure(self):
        """Что тестируем: заголовок Strict-Transport-Security.
        Что передаём: политику с ``cookie_secure`` False и затем True.
        Что ожидаем: HSTS появляется только при защищённых куках — в HTTP-среде
        он был бы бесполезен, а включённый заранее сломал бы доступ.
        """
        insecure = await _headers(cookie_secure=False)
        secure = await _headers(cookie_secure=True)

        assert "strict-transport-security" not in insecure
        assert secure["strict-transport-security"].startswith("max-age=63072000")

    async def test_baseline_headers_are_present(self):
        """Что тестируем: базовые заголовки защиты.
        Что передаём: любой ответ.
        Что ожидаем: ``X-Frame-Options: DENY``, ``X-Content-Type-Options: nosniff``,
        ``Referrer-Policy: same-origin``.
        """
        headers = await _headers(cookie_secure=False)

        assert headers["x-frame-options"] == "DENY"
        assert headers["x-content-type-options"] == "nosniff"
        assert headers["referrer-policy"] == "same-origin"
