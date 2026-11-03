"""Интеграционные тесты JSON-аутентификации и конфигурации API (этап 8).

Проверяется контракт мобильного клиента: пара токенов в теле вместо cookie,
единая форма отказа ``{code, message, details}``, отзыв токенов по Bearer и
фиче-флаги, которые клиент читает перед построением интерфейса.
"""

from __future__ import annotations

import pytest
from dishka import AsyncContainer, Provider, Scope, make_async_container, provide
from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from backend.application.dto import LoginCommand, LogoutCommand, RefreshSessionCommand
from backend.application.dto.auth import GoogleSignInCommand
from backend.application.interface.services import JWTServiceInterface, RateLimiterInterface
from backend.application.interface.services.token_blocklist import TokenBlocklistInterface
from backend.application.policies import (
    ApiFeatureFlags,
    AppReleaseInfo,
    CookiePolicy,
    ProxyTrustPolicy,
)
from backend.application.use_cases import (
    GoogleSignInUseCase,
    LoginUserUseCase,
    LogoutUserUseCase,
    RefreshSessionUseCase,
)
from backend.application.use_cases.auth.result import AuthResult
from backend.application.use_cases.result import UseCaseResult
from backend.domain import User
from backend.infrastructure.cache.key_value_store import KeyValueStore
from backend.infrastructure.security.rate_limiter import RateLimiter
from backend.presentation.api.errors import register_exception_handlers
from backend.presentation.api.v1.auth import api_auth_router
from backend.presentation.api.v1.config import api_config_router

USER_ID = 5
REFRESH_TOKEN = "refresh-token-5-for-rotation"
ACCESS_TTL_SECONDS = 900
REFRESH_TTL_SECONDS = 86400
SESSION_USER = User(
    email="user@example.com",
    password_hash="hash",
    username="tester",
    id=USER_ID,
)


def _result(ok: bool) -> AuthResult:
    """Собрать итог сценария аутентификации: пользователя либо отказ.

    Args:
        ok: True — успешный результат с пользователем сессии.

    Returns:
        AuthResult: Результат для двойника сценария.
    """
    if ok:
        return AuthResult(ok=True, data=SESSION_USER)
    return AuthResult(ok=False, error_message="отказано", error_endpoint="auth.login_page")


class _RecordingUseCase:
    """Базовая заглушка сценария аутентификации с журналом вызовов."""

    def __init__(self, result: AuthResult) -> None:
        """Сохранить подготовленный итог и создать журнал вызовов.

        Args:
            result: Результат, который возвращает сценарий.
        """
        self.result = result
        self.calls: list[object] = []


class _FakeLogin(_RecordingUseCase):
    """Заглушка сценария входа."""

    async def execute(self, command: LoginCommand) -> AuthResult:
        """Запомнить команду и вернуть подготовленный итог."""
        self.calls.append(command)
        return self.result


class _FakeRefresh(_RecordingUseCase):
    """Заглушка сценария продления сессии."""

    async def execute(self, command: RefreshSessionCommand) -> AuthResult:
        """Запомнить refresh-токен и вернуть подготовленный итог."""
        self.calls.append(command)
        return self.result


class _FakeLogout(_RecordingUseCase):
    """Заглушка сценария выхода с отзывом токенов."""

    async def execute(self, command: LogoutCommand) -> AuthResult:
        """Запомнить отзываемые токены и вернуть успех."""
        self.calls.append(command)
        return self.result


class _FakeGoogleSignIn:
    """Заглушка сценария входа через Google с результатом прикладного слоя."""

    def __init__(self, result: UseCaseResult) -> None:
        """Сохранить подготовленный итог."""
        self.result = result
        self.calls: list[object] = []

    async def execute(self, command: GoogleSignInCommand) -> UseCaseResult:
        """Запомнить команду и вернуть подготовленный итог."""
        self.calls.append(command)
        return self.result


class _FakeJWT:
    """Двойник JWT-сервиса с предсказуемыми значениями токенов."""

    async def create_access_token(self, user_id: int) -> str:
        """Вернуть детерминированный access-токен."""
        return f"access-{user_id}"

    async def create_refresh_token(self, user_id: int) -> str:
        """Вернуть детерминированный refresh-токен."""
        return f"refresh-{user_id}"


class _FakeBlocklist:
    """Двойник списка отозванных, принимающий отзывы без хранения."""

    async def revoke(self, token: str, ttl_seconds: int) -> None:
        """Принять отзыв токена."""
        return None


class _ApiProvider(Provider):
    """Зависимости тестового приложения: сценарии, JWT, лимитер и флаги."""

    def __init__(
        self,
        *,
        login: _FakeLogin,
        refresh: _FakeRefresh,
        logout: _FakeLogout,
        google_sign_in: _FakeGoogleSignIn,
        flags: ApiFeatureFlags,
    ) -> None:
        """Сохранить подготовленные двойники сценариев."""
        super().__init__()
        self._login = login
        self._refresh = refresh
        self._logout = logout
        self._google_sign_in = google_sign_in
        self._flags = flags

    @provide(scope=Scope.APP)
    def rate_limiter(self) -> RateLimiterInterface:
        """Отдать лимитер на in-memory хранилище без Redis."""
        return RateLimiter(KeyValueStore(redis_url=None, namespace="api_auth"))

    @provide(scope=Scope.APP)
    def proxy_trust_policy(self) -> ProxyTrustPolicy:
        """Отдать политику без доверенных прокси."""
        return ProxyTrustPolicy(trusted_proxies=())

    @provide(scope=Scope.APP)
    def cookie_policy(self) -> CookiePolicy:
        """Отдать политику cookie с известными сроками жизни токенов."""
        return CookiePolicy(
            secure=False,
            samesite="Lax",
            domain=None,
            access_expire_minutes=ACCESS_TTL_SECONDS // 60,
            refresh_expire_days=REFRESH_TTL_SECONDS // 86400,
        )

    @provide(scope=Scope.APP)
    def api_feature_flags(self) -> ApiFeatureFlags:
        """Отдать подготовленный набор фиче-флагов."""
        return self._flags

    @provide(scope=Scope.APP)
    def app_release_info(self) -> AppReleaseInfo:
        """Отдать релиз мобильного приложения по умолчанию."""
        return AppReleaseInfo()

    @provide(scope=Scope.REQUEST)
    def jwt_service(self) -> JWTServiceInterface:
        """Отдать двойник сервиса токенов."""
        return _FakeJWT()

    @provide(scope=Scope.REQUEST)
    def token_blocklist(self) -> TokenBlocklistInterface:
        """Отдать двойник списка отозванных токенов."""
        return _FakeBlocklist()

    @provide(scope=Scope.REQUEST)
    def login_user(self) -> LoginUserUseCase:
        """Отдать заглушку сценария входа."""
        return self._login

    @provide(scope=Scope.REQUEST)
    def refresh_session(self) -> RefreshSessionUseCase:
        """Отдать заглушку сценария продления."""
        return self._refresh

    @provide(scope=Scope.REQUEST)
    def logout_user(self) -> LogoutUserUseCase:
        """Отдать заглушку сценария выхода."""
        return self._logout

    @provide(scope=Scope.REQUEST)
    def google_sign_in(self) -> GoogleSignInUseCase:
        """Отдать заглушку сценария входа через Google."""
        return self._google_sign_in


def build_api_client(
    *,
    login: _FakeLogin | None = None,
    refresh: _FakeRefresh | None = None,
    logout: _FakeLogout | None = None,
    google_sign_in: _FakeGoogleSignIn | None = None,
    flags: ApiFeatureFlags | None = None,
) -> tuple[TestClient, dict[str, object]]:
    """Собрать приложение с JSON-маршрутами аутентификации и конфигурации.

    Args:
        login: Заглушка сценария входа.
        refresh: Заглушка сценария продления.
        logout: Заглушка сценария выхода.
        google_sign_in: Заглушка сценария входа через Google.
        flags: Набор фиче-флагов для ``/api/v1/config``.

    Returns:
        tuple[TestClient, dict[str, object]]: Клиент и словарь двойников.
    """
    doubles = {
        "login": login or _FakeLogin(_result(False)),
        "refresh": refresh or _FakeRefresh(_result(False)),
        "logout": logout or _FakeLogout(_result(True)),
        "google_sign_in": google_sign_in
        or _FakeGoogleSignIn(
            UseCaseResult.failure("Недействительный токен Google", status_code=401)
        ),
    }
    app = FastAPI()
    container: AsyncContainer = make_async_container(
        _ApiProvider(
            login=doubles["login"],
            refresh=doubles["refresh"],
            logout=doubles["logout"],
            google_sign_in=doubles["google_sign_in"],
            flags=flags or ApiFeatureFlags(),
        )
    )

    @app.middleware("http")
    async def inject_state(request: Request, call_next):
        """Очистить состояние запроса перед маршрутом."""
        request.state.user = None
        return await call_next(request)

    app.include_router(api_auth_router)
    app.include_router(api_config_router)
    register_exception_handlers(app)
    setup_dishka(container=container, app=app)
    return TestClient(app, headers={"Accept": "application/json"}), doubles


@pytest.mark.integration
class TestApiTokenIssue:
    """Выпуск пары токенов по учётным данным."""

    def test_returns_token_pair(self):
        """Что тестируем: POST /api/v1/auth/token успешными учётными данными.
        Что передаём: почту в верхнем регистре и пароль.
        Что ожидаем: 200 с парой токенов, сроком жизни и данными пользователя.
        """
        client, doubles = build_api_client(login=_FakeLogin(_result(True)))

        response = client.post(
            "/api/v1/auth/token",
            json={"email": "User@Example.com", "password": "secret-pass"},
        )

        assert response.status_code == 200
        assert response.json() == {
            "access_token": f"access-{USER_ID}",
            "refresh_token": f"refresh-{USER_ID}",
            "token_type": "bearer",
            "access_expires_in": ACCESS_TTL_SECONDS,
            "refresh_expires_in": REFRESH_TTL_SECONDS,
            "user_id": USER_ID,
            "username": "tester",
            "email": "user@example.com",
        }
        assert doubles["login"].calls[0].email == "user@example.com"

    def test_rejects_bad_credentials_with_unified_error(self):
        """Что тестируем: отказ при неверных учётных данных.
        Что передаём: команду, которую сценарий отклонил.
        Что ожидаем: 401 с единым телом ``code``/``message``.
        """
        client, _doubles = build_api_client(login=_FakeLogin(_result(False)))

        response = client.post(
            "/api/v1/auth/token",
            json={"email": "user@example.com", "password": "secret-pass"},
        )

        assert response.status_code == 401
        assert response.json() == {"code": "unauthorized", "message": "отказано"}

    def test_rejects_missing_password_with_validation_details(self):
        """Что тестируем: защиту тела запроса схемой Pydantic.
        Что передаём: тело без пароля.
        Что ожидаем: 422 с перечнем проблемных полей в ``details``.
        """
        client, doubles = build_api_client(login=_FakeLogin(_result(True)))

        response = client.post("/api/v1/auth/token", json={"email": "user@example.com"})

        assert response.status_code == 422
        body = response.json()
        assert body["code"] == "validation_failed"
        assert [item["location"] for item in body["details"]["fields"]] == ["body.password"]
        assert doubles["login"].calls == []


@pytest.mark.integration
class TestApiTokenRefresh:
    """Продление пары токенов по refresh-значению."""

    def test_returns_rotated_pair(self):
        """Что тестируем: POST /api/v1/auth/token/refresh действующим токеном.
        Что передаём: тело с refresh-токеном.
        Что ожидаем: 200 с новой парой и данными того же пользователя.
        """
        client, doubles = build_api_client(refresh=_FakeRefresh(_result(True)))

        response = client.post("/api/v1/auth/token/refresh", json={"refresh_token": REFRESH_TOKEN})

        assert response.status_code == 200
        payload = response.json()
        assert payload["access_token"] == f"access-{USER_ID}"
        assert payload["refresh_token"] == f"refresh-{USER_ID}"
        assert doubles["refresh"].calls[0].refresh_token == REFRESH_TOKEN

    def test_rejects_expired_session(self):
        """Что тестируем: отказ продления истёкшей сессии.
        Что передаём: сценарий, вернувший ошибку.
        Что ожидаем: 401 с текстом сценария в едином теле.
        """
        client, _doubles = build_api_client(refresh=_FakeRefresh(_result(False)))

        response = client.post("/api/v1/auth/token/refresh", json={"refresh_token": REFRESH_TOKEN})

        assert response.status_code == 401
        assert response.json() == {"code": "unauthorized", "message": "отказано"}


@pytest.mark.integration
class TestApiTokenRevoke:
    """Отзыв токенов мобильным клиентом."""

    def test_requires_bearer_header(self):
        """Что тестируем: отзыв без заголовка Authorization.
        Что передаём: тело с refresh-токеном и отсутствие Bearer.
        Что ожидаем: 401, сценарий выхода не вызывается.
        """
        client, doubles = build_api_client()

        response = client.post("/api/v1/auth/token/revoke", json={"refresh_token": REFRESH_TOKEN})

        assert response.status_code == 401
        assert response.json()["code"] == "unauthorized"
        assert doubles["logout"].calls == []

    def test_revokes_both_tokens(self):
        """Что тестируем: отзыв пары токенов авторизованным клиентом.
        Что передаём: Bearer-заголовок с access-токеном и тело с refresh-токеном.
        Что ожидаем: 200 с признаком отзыва, сценарий вызван с обоими значениями.
        """
        client, doubles = build_api_client()

        response = client.post(
            "/api/v1/auth/token/revoke",
            json={"refresh_token": REFRESH_TOKEN},
            headers={"Authorization": "Bearer access-5"},
        )

        assert response.status_code == 200
        assert response.json() == {"revoked": True}
        assert doubles["logout"].calls[0] == LogoutCommand(
            access_token="access-5", refresh_token=REFRESH_TOKEN
        )


@pytest.mark.integration
class TestApiConfig:
    """Фиче-флаги, которые клиент узнаёт до построения интерфейса."""

    def test_reports_disabled_flags_by_default(self):
        """Что тестируем: GET /api/v1/config с флагами по умолчанию.
        Что передаём: пустые флаги и пустой релиз.
        Что ожидаем: версия API, два выключенных разрешения и пустые поля релиза.
        """
        client, _doubles = build_api_client()

        response = client.get("/api/v1/config")

        assert response.status_code == 200
        assert response.json() == {
            "api_version": "v1",
            "adult_sources_enabled": False,
            "manual_source_creation_enabled": False,
            "latest_app_version": "",
            "min_app_version": "",
            "apk_url": "",
            "apk_sha256": "",
            "changelog_url": "",
            "maintenance_mode": False,
        }

    def test_reports_enabled_flags(self):
        """Что тестируем: тот же маршрут при включённых разрешениях.
        Что передаём: флаги взрослого контента и ручных источников.
        Что ожидаем: значения, доведённые до клиента без искажений.
        """
        client, _doubles = build_api_client(
            flags=ApiFeatureFlags(adult_sources_enabled=True, manual_source_creation_enabled=True)
        )

        payload = client.get("/api/v1/config").json()

        assert payload["adult_sources_enabled"] is True
        assert payload["manual_source_creation_enabled"] is True


@pytest.mark.integration
class TestApiGoogleSignIn:
    """Вход мобильного клиента через Google с выпуском пары токенов."""

    def test_returns_token_pair_for_verified_identity(self):
        """Что тестируем: POST /api/v1/auth/google при подтверждённой личности.
        Что передаём: ID-токен, сценарий возвращает пользователя сессии.
        Что ожидаем: 200 с парой токенов и данными пользователя.
        """
        client, doubles = build_api_client(
            google_sign_in=_FakeGoogleSignIn(UseCaseResult.success(SESSION_USER))
        )

        response = client.post("/api/v1/auth/google", json={"id_token": "google-id-token-value"})

        assert response.status_code == 200
        payload = response.json()
        assert payload["access_token"] == f"access-{USER_ID}"
        assert payload["refresh_token"] == f"refresh-{USER_ID}"
        assert payload["user_id"] == USER_ID
        assert doubles["google_sign_in"].calls[0].id_token == "google-id-token-value"

    def test_returns_unified_error_for_invalid_token(self):
        """Что тестируем: отказ входа при непроверенном токене.
        Что передаём: сценарий вернул отказ 401.
        Что ожидаем: 401 с единым телом и текстом сценария.
        """
        client, _doubles = build_api_client(
            google_sign_in=_FakeGoogleSignIn(
                UseCaseResult.failure("Недействительный токен Google", status_code=401)
            )
        )

        response = client.post("/api/v1/auth/google", json={"id_token": "google-id-token-value"})

        assert response.status_code == 401
        assert response.json() == {
            "code": "unauthorized",
            "message": "Недействительный токен Google",
        }

    def test_rejects_short_id_token_with_validation(self):
        """Что тестируем: схему тела запроса Google.
        Что передаём: id_token короче минимальной длины.
        Что ожидаем: 422 и сценарий не вызван.
        """
        client, doubles = build_api_client(
            google_sign_in=_FakeGoogleSignIn(UseCaseResult.success(SESSION_USER))
        )

        response = client.post("/api/v1/auth/google", json={"id_token": "short"})

        assert response.status_code == 422
        assert doubles["google_sign_in"].calls == []
