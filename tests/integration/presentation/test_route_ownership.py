"""Интеграционные тесты проверки владельца ресурса (задача S1).

Проверяется контракт: приватные роуты берут идентификатор пользователя только
из аутентифицированной сессии, анонимный запрос получает 401, а запрос
пользователя A к ресурсу пользователя B — 403. Публичные роуты (публичный
профиль, чужие хайлайты) обязаны оставаться доступными гостям.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from dishka import AsyncContainer, Provider, Scope, make_async_container, provide
from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
from fastapi.testclient import TestClient

from backend.application.interface.services import RateLimiterInterface
from backend.application.policies import ProxyTrustPolicy
from backend.application.use_cases import (
    AskAiRecommendationsUseCase,
    GenerateRecommendationsUseCase,
    GetFavoriteIdsUseCase,
    GetFavoritesUseCase,
    RefreshRecommendationsUseCase,
    SetUserFollowUseCase,
)
from backend.domain import RecommendationResult
from backend.infrastructure.cache.key_value_store import KeyValueStore
from backend.infrastructure.security.rate_limiter import RateLimiter
from backend.presentation.api.errors import register_exception_handlers
from backend.presentation.api.v1.favorite_route import favorite_router
from backend.presentation.api.v1.recommendation_route import recommendation_router
from backend.presentation.api.v1.user_route import user_router

OWNER_ID = 5
INTRUDER_ID = 6
JSON_ACCEPT = {"Accept": "application/json"}


class _FakeFavorites:
    """Заглушки сценариев избранного, возвращающие предсказуемый ответ."""

    def __init__(self) -> None:
        """Создать заглушки со счётчиком вызовов."""
        self.calls: list[int] = []

    async def execute(self, query):
        """Запомнить запрошенный идентификатор и вернуть пустой список.

        Args:
            query: Запрос сценария избранного с полем ``user_id``.

        Returns:
            list: Пустой список идентификаторов.
        """
        self.calls.append(query.user_id)
        return []


class _FakeRecommendations:
    """Заглушка сценариев рекомендаций, отвечающая списком."""

    def __init__(self) -> None:
        """Создать заглушку со счётчиком вызовов."""
        self.calls: list[int] = []

    async def execute(self, query):
        """Запомнить аргументы и вернуть одну рекомендацию.

        Args:
            query: Query-объект с ``user_id`` и лимитом.

        Returns:
            list[RecommendationResult]: Список из одной рекомендации.
        """
        self.calls.append(query.user_id)
        return [_recommendation(1)]


class _FakeAskRecommendations:
    """Заглушка AI-рекомендаций, отвечающая объектом результата."""

    def __init__(self) -> None:
        """Создать заглушку со счётчиком вызовов."""
        self.calls: list[object] = []

    async def execute(self, command):
        """Запомнить команду и вернуть успешный результат.

        Args:
            command: Команда запроса рекомендаций.

        Returns:
            SimpleNamespace: Результат с полем ``ok`` и списком данных.
        """
        self.calls.append(command)
        return SimpleNamespace(ok=True, data=[_recommendation(1)], status_code=200)


def _recommendation(anime_id: int) -> RecommendationResult:
    """Собрать настоящую рекомендацию для проверки JSON-модели ответа."""
    return RecommendationResult(
        anime_id=anime_id,
        reason="Проверка владения",
        similarity_score=0.5,
        title="Рекомендация",
        description="Описание",
        image_url=None,
        genres=["Action"],
        watch_url=f"/watch/{anime_id}?episode=1",
    )


class _FakeFollow:
    """Заглушка подписки, возвращающая успешный результат."""

    def __init__(self) -> None:
        """Создать заглушку со списком вызовов."""
        self.calls: list[tuple[object, object]] = []

    async def execute(self, command):
        """Запомнить пару участников и вернуть состояние подписки.

        Args:
            command: Команда подписки с идентификаторами сторон и флагом.

        Returns:
            SimpleNamespace: Результат с полем ``ok`` и состоянием подписки.
        """
        self.calls.append((command.follower_user_id, command.followed_user_id))
        return SimpleNamespace(ok=True, data=command.follow, error=None, status_code=200)


class _TestProvider(Provider):
    """Провайдер фейковых сценариев и лимитера для тестового приложения."""

    def __init__(
        self,
        favorites: _FakeFavorites,
        recommendations: _FakeRecommendations,
        ask: _FakeAskRecommendations,
        follow: _FakeFollow | None = None,
    ) -> None:
        """Сохранить экземпляры сценариев.

        Args:
            favorites: Заглушка сценариев избранного.
            recommendations: Заглушка сценариев рекомендаций.
            ask: Заглушка AI-рекомендаций.
            follow: Заглушка подписки, создаётся при отсутствии.
        """
        super().__init__()
        self._favorites = favorites
        self._recommendations = recommendations
        self._ask = ask
        self._follow = follow or _FakeFollow()

    @provide(scope=Scope.APP)
    def rate_limiter(self) -> RateLimiterInterface:
        """Отдать лимитер на in-memory хранилище.

        Returns:
            RateLimiterInterface: Работающий без Redis лимитер.
        """
        return RateLimiter(KeyValueStore(redis_url=None, namespace="ownership"))

    @provide(scope=Scope.APP)
    def proxy_trust_policy(self) -> ProxyTrustPolicy:
        """Отдать политику доверенных прокси без доверенных адресов.

        Returns:
            ProxyTrustPolicy: Пустой список — X-Forwarded-For не принимается.
        """
        return ProxyTrustPolicy(trusted_proxies=())

    @provide(scope=Scope.REQUEST)
    def get_favorites(self) -> GetFavoritesUseCase:
        """Отдать сценарий списка избранного.

        Returns:
            GetFavoritesUseCase: Заглушка сценария.
        """
        return self._favorites

    @provide(scope=Scope.REQUEST)
    def get_favorite_ids(self) -> GetFavoriteIdsUseCase:
        """Отдать сценарий идентификаторов избранного.

        Returns:
            GetFavoriteIdsUseCase: Заглушка сценария.
        """
        return self._favorites

    @provide(scope=Scope.REQUEST)
    def generate_recommendations(self) -> GenerateRecommendationsUseCase:
        """Отдать сценарий генерации рекомендаций.

        Returns:
            GenerateRecommendationsUseCase: Заглушка сценария.
        """
        return self._recommendations

    @provide(scope=Scope.REQUEST)
    def refresh_recommendations(self) -> RefreshRecommendationsUseCase:
        """Отдать сценарий обновления рекомендаций.

        Returns:
            RefreshRecommendationsUseCase: Заглушка сценария.
        """
        return self._recommendations

    @provide(scope=Scope.REQUEST)
    def ask_recommendations(self) -> AskAiRecommendationsUseCase:
        """Отдать сценарий AI-рекомендаций.

        Returns:
            AskAiRecommendationsUseCase: Заглушка сценария.
        """
        return self._ask

    @provide(scope=Scope.REQUEST)
    def follow_user(self) -> SetUserFollowUseCase:
        """Отдать сценарий подписки на пользователя.

        Returns:
            SetUserFollowUseCase: Заглушка сценария.
        """
        return self._follow


def build_client(
    user: object | None,
    favorites: _FakeFavorites,
    recommendations: _FakeRecommendations,
    ask: _FakeAskRecommendations,
) -> TestClient:
    """Собрать тестовое приложение с указанным пользователем сессии.

    Args:
        user: Пользователь сессии либо None для анонимного запроса.
        favorites: Заглушка сценариев избранного.
        recommendations: Заглушка сценариев рекомендаций.
        ask: Заглушка AI-рекомендаций.

    Returns:
        TestClient: Клиент для обращения к роутам.
    """
    app = FastAPI()
    container: AsyncContainer = make_async_container(_TestProvider(favorites, recommendations, ask))

    @app.middleware("http")
    async def inject_state(request: Request, call_next):
        """Прикрепить пользователя сессии к запросу.

        Args:
            request: Текущий HTTP-запрос.
            call_next: Следующий шаг обработки.

        Returns:
            Response: Ответ роута.
        """
        request.state.user = user
        return await call_next(request)

    app.include_router(favorite_router)
    app.include_router(recommendation_router)
    register_exception_handlers(app)
    setup_dishka(container=container, app=app)
    return TestClient(app, headers=JSON_ACCEPT)


@pytest.mark.integration
class TestFavoritesOwnership:
    """Проверка владельца для роутов избранного."""

    def test_guest_gets_401_on_favorite_ids(self):
        """Что тестируем: GET /favorites/ids/{user_id} без сессии.
        Что передаём: анонимный запрос.
        Что ожидаем: 401, сценарий не вызывается.
        """
        favorites = _FakeFavorites()
        client = build_client(None, favorites, _FakeRecommendations(), _FakeAskRecommendations())

        response = client.get(f"/favorites/ids/{OWNER_ID}")

        assert response.status_code == 401
        assert favorites.calls == []

    def test_foreign_user_gets_403_on_favorite_ids(self):
        """Что тестируем: GET /favorites/ids/{user_id} чужим пользователем.
        Что передаём: сессию пользователя 6 и путь с идентификатором 5.
        Что ожидаем: 403, сценарий не вызывается.
        """
        favorites = _FakeFavorites()
        client = build_client(
            SimpleNamespace(id=INTRUDER_ID),
            favorites,
            _FakeRecommendations(),
            _FakeAskRecommendations(),
        )

        response = client.get(f"/favorites/ids/{OWNER_ID}")

        assert response.status_code == 403
        assert favorites.calls == []

    def test_owner_gets_favorite_ids(self):
        """Что тестируем: GET /favorites/ids/{user_id} владельцем.
        Что передаём: сессию пользователя 5 и тот же идентификатор в пути.
        Что ожидаем: 200 со списком идентификаторов.
        """
        favorites = _FakeFavorites()
        client = build_client(
            SimpleNamespace(id=OWNER_ID),
            favorites,
            _FakeRecommendations(),
            _FakeAskRecommendations(),
        )

        response = client.get(f"/favorites/ids/{OWNER_ID}")

        assert response.status_code == 200
        assert response.json() == {"user_id": OWNER_ID, "anime_ids": []}

    def test_guest_gets_401_on_favorites_page(self):
        """Что тестируем: GET /favorites/{user_id} без сессии.
        Что передаём: анонимный запрос.
        Что ожидаем: 401, избрание чужого пользователя не отдаётся.
        """
        favorites = _FakeFavorites()
        client = build_client(None, favorites, _FakeRecommendations(), _FakeAskRecommendations())

        response = client.get(f"/favorites/{OWNER_ID}")

        assert response.status_code == 401

    def test_foreign_user_gets_403_on_favorites_page(self):
        """Что тестируем: GET /favorites/{user_id} чужим пользователем.
        Что передаём: сессию пользователя 6 и путь с идентификатором 5.
        Что ожидаем: 403.
        """
        favorites = _FakeFavorites()
        client = build_client(
            SimpleNamespace(id=INTRUDER_ID),
            favorites,
            _FakeRecommendations(),
            _FakeAskRecommendations(),
        )

        response = client.get(f"/favorites/{OWNER_ID}")

        assert response.status_code == 403


@pytest.mark.integration
class TestRecommendationsOwnership:
    """Проверка владельца для роутов рекомендаций (в том числе расход LLM-квоты)."""

    @pytest.mark.parametrize("action", ["generate", "refresh"])
    def test_guest_gets_401(self, action: str):
        """Что тестируем: POST /api/v1/recommendations/{action}/{user_id} без сессии.
        Что передаём: анонимный запрос для generate и refresh.
        Что ожидаем: 401, сценарий не вызывается.
        """
        recommendations = _FakeRecommendations()
        client = build_client(None, _FakeFavorites(), recommendations, _FakeAskRecommendations())

        response = client.post(f"/api/v1/recommendations/{action}/{OWNER_ID}")

        assert response.status_code == 401
        assert recommendations.calls == []

    @pytest.mark.parametrize("action", ["generate", "refresh"])
    def test_foreign_user_gets_403(self, action: str):
        """Что тестируем: POST /api/v1/recommendations/{action}/{user_id} чужим пользователем.
        Что передаём: сессию пользователя 6 и путь с идентификатором 5.
        Что ожидаем: 403, чужие рекомендации не генерируются.
        """
        recommendations = _FakeRecommendations()
        client = build_client(
            SimpleNamespace(id=INTRUDER_ID),
            _FakeFavorites(),
            recommendations,
            _FakeAskRecommendations(),
        )

        response = client.post(f"/api/v1/recommendations/{action}/{OWNER_ID}")

        assert response.status_code == 403
        assert recommendations.calls == []

    def test_owner_can_generate(self):
        """Что тестируем: POST /api/v1/recommendations/generate/{user_id} владельцем.
        Что передаём: сессию пользователя 5 и тот же идентификатор в пути.
        Что ожидаем: 200, сценарий вызван для пользователя 5.
        """
        recommendations = _FakeRecommendations()
        client = build_client(
            SimpleNamespace(id=OWNER_ID),
            _FakeFavorites(),
            recommendations,
            _FakeAskRecommendations(),
        )

        response = client.post(f"/api/v1/recommendations/generate/{OWNER_ID}")

        assert response.status_code == 200
        assert recommendations.calls == [OWNER_ID]

    def test_guest_cannot_ask_ai(self):
        """Что тестируем: POST /api/v1/recommendations/ask/{user_id} без сессии.
        Что передаём: анонимный запрос с текстом вопроса.
        Что ожидаем: 401, обращений к LLM нет.
        """
        ask = _FakeAskRecommendations()
        client = build_client(None, _FakeFavorites(), _FakeRecommendations(), ask)

        response = client.post(
            f"/api/v1/recommendations/ask/{OWNER_ID}",
            json={"query": "что-нибудь про космос"},
        )

        assert response.status_code == 401
        assert ask.calls == []

    def test_foreign_user_cannot_ask_ai(self):
        """Что тестируем: POST /api/v1/recommendations/ask/{user_id} чужим пользователем.
        Что передаём: сессию пользователя 6 и идентификатор 5 в пути.
        Что ожидаем: 403, чужая LLM-квота и чужие избранные тайтлы не расходуются.
        """
        ask = _FakeAskRecommendations()
        client = build_client(
            SimpleNamespace(id=INTRUDER_ID),
            _FakeFavorites(),
            _FakeRecommendations(),
            ask,
        )

        response = client.post(
            f"/api/v1/recommendations/ask/{OWNER_ID}",
            json={"query": "что-нибудь про космос"},
        )

        assert response.status_code == 403
        assert ask.calls == []

    def test_owner_can_ask_ai(self):
        """Что тестируем: POST /api/v1/recommendations/ask/{user_id} владельцем.
        Что передаём: сессию пользователя 5, тот же идентификатор в пути и вопрос.
        Что ожидаем: 200, команда построена для пользователя 5.
        """
        ask = _FakeAskRecommendations()
        client = build_client(
            SimpleNamespace(id=OWNER_ID), _FakeFavorites(), _FakeRecommendations(), ask
        )

        response = client.post(
            f"/api/v1/recommendations/ask/{OWNER_ID}",
            json={"query": "что-нибудь про космос"},
        )

        assert response.status_code == 200
        assert ask.calls[0].user_id == OWNER_ID


def build_follow_client(user: object | None, follow: _FakeFollow) -> TestClient:
    """Собрать приложение с роутами пользователей.

    Args:
        user: Пользователь сессии либо None для анонимного запроса.
        follow: Заглушка сценария подписки.

    Returns:
        TestClient: Клиент для обращения к роутам подписки.
    """
    app = FastAPI()
    container: AsyncContainer = make_async_container(
        _TestProvider(_FakeFavorites(), _FakeRecommendations(), _FakeAskRecommendations(), follow)
    )

    @app.middleware("http")
    async def inject_state(request: Request, call_next):
        """Прикрепить пользователя сессии к запросу.

        Args:
            request: Текущий HTTP-запрос.
            call_next: Следующий шаг обработки.

        Returns:
            Response: Ответ роута.
        """
        request.state.user = user
        return await call_next(request)

    app.include_router(user_router)

    async def login_page() -> PlainTextResponse:
        """Заглушка страницы входа для редиректов гостя.

        Returns:
            PlainTextResponse: Текст-заглушка.
        """
        return PlainTextResponse("login")

    app.add_api_route("/auth/login", login_page, methods=["GET"], name="auth.login_page")
    register_exception_handlers(app)
    setup_dishka(container=container, app=app)
    return TestClient(app, headers=JSON_ACCEPT)


@pytest.mark.integration
class TestFollowAuthentication:
    """Подписка работает только как форма страницы: гость получает редирект."""

    def test_json_guest_is_redirected_to_login(self):
        """Что тестируем: POST /users/{user_id}/follow без сессии из JSON-клиента.
        Что передаём: запрос с Accept: application/json.
        Что ожидаем: 303 на страницу входа — JSON-ветки у формы подписки нет.
        """
        follow = _FakeFollow()
        client = build_follow_client(None, follow)

        response = client.post(
            f"/users/{OWNER_ID}/follow",
            headers={"Accept": "application/json"},
            follow_redirects=False,
        )

        assert response.status_code == 303
        assert follow.calls == []

    def test_page_guest_is_redirected_to_login(self):
        """Что тестируем: POST /users/{user_id}/follow без сессии из браузера.
        Что передаём: обычный запрос без Accept: application/json.
        Что ожидаем: 303 на страницу входа — поведение страницы сохранено.
        """
        follow = _FakeFollow()
        client = build_follow_client(None, follow)

        response = client.post(f"/users/{OWNER_ID}/follow", follow_redirects=False)

        assert response.status_code == 303
        assert follow.calls == []

    def test_signed_user_follows(self):
        """Что тестируем: POST /users/{user_id}/follow владельцем сессии.
        Что передаём: сессию пользователя 6 и цель подписки 5.
        Что ожидаем: 303 в профиль цели, сценарий вызван с инициатором из сессии.
        """
        follow = _FakeFollow()
        client = build_follow_client(SimpleNamespace(id=INTRUDER_ID), follow)

        response = client.post(
            f"/users/{OWNER_ID}/follow",
            headers={"Accept": "application/json"},
            follow_redirects=False,
        )

        assert response.status_code == 303
        assert response.headers["location"] == f"/users/{OWNER_ID}"
        assert follow.calls == [(INTRUDER_ID, OWNER_ID)]
